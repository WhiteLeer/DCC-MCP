"""Persistent Houdini daemon for GUI control and MCP bridging."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Set

import psutil
import websockets
from websockets.server import WebSocketServerProtocol

from houdini_mcp.connection_manager import HoudiniConnectionManager
from houdini_mcp.houdini_session import HoudiniSessionBackend
from houdini_mcp.utils.logging_config import setup_logging
from houdini_mcp.utils.state_paths import (
    get_lock_file,
    get_ws_port_file,
    get_ws_port_instance_file,
)
from houdini_mcp.utils.houdini_paths import resolve_hython_path
from houdini_mcp.websocket_protocol import (
    MessageType,
    WSMessage,
    error_message,
    log_message,
    operation_log,
    process_count_message,
    status_update,
)

logger = setup_logging(
    name="houdini-mcp-daemon",
    log_level="INFO",
    enable_file_logging=True,
    enable_console_logging=True,
)


class HoudiniDaemon:
    def __init__(self, hython_path: str, host: str = "127.0.0.1", port: int = 9876):
        self.host = host
        self.port = port
        self.hython_path = hython_path
        self.session = HoudiniSessionBackend(str(Path(hython_path).parent))
        self.connection_manager = HoudiniConnectionManager(hython_path)
        self.connection_manager.connect()
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server: Optional[websockets.WebSocketServer] = None
        self.start_time = time.time()
        self.stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "operation_times": [],
        }

    async def start(self) -> None:
        original_port = self.port
        for _ in range(10):
            try:
                self.server = await websockets.serve(self._handle_client, self.host, self.port)
                break
            except OSError:
                self.port += 1
        if self.server is None:
            raise RuntimeError(f"Failed to bind daemon WebSocket port starting from {original_port}")
        self._write_state_files()
        logger.info(f"Daemon listening on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        self._cleanup_state_files()

    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str | None = None) -> None:
        client_addr = websocket.remote_address
        logger.debug(f"Client connected: {client_addr}")
        self.clients.add(websocket)
        try:
            await self._send_status(websocket)
            async for message in websocket:
                await self._handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.debug(f"Client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}", exc_info=True)
            try:
                await websocket.send(error_message(str(e)).to_json())
            except Exception:
                pass
        finally:
            self.clients.discard(websocket)

    async def _handle_message(self, websocket: WebSocketServerProtocol, raw: str) -> None:
        message = WSMessage.from_json(raw)

        if message.type == MessageType.GET_STATUS:
            await self._send_status(websocket)
            return
        if message.type == MessageType.GET_PROCESS_COUNT:
            await self._send_process_count(websocket)
            return
        if message.type == MessageType.RESTART_HOUDINI:
            await self._restart_houdini()
            await self._send_status(websocket)
            return
        if message.type == MessageType.RELOAD_CONFIG:
            self.connection_manager.reload_config(message.data)
            await self.broadcast(log_message("INFO", "Configuration reloaded", datetime.now().isoformat()))
            await self._send_status(websocket)
            return
        if message.type == MessageType.CLEAR_CACHE:
            self.connection_manager.clear_cache()
            await self.broadcast(log_message("INFO", "Cache cleared", datetime.now().isoformat()))
            return
        if message.type == MessageType.UPDATE_TIMEOUT:
            await websocket.send(log_message("INFO", "Timeout update acknowledged", datetime.now().isoformat()).to_json())
            return
        if message.type == MessageType.SHUTDOWN:
            await self.broadcast(log_message("WARNING", "Daemon shutdown requested", datetime.now().isoformat()))
            asyncio.create_task(self._shutdown_soon())
            return
        if message.type == MessageType.RESTART_MCP_SERVER:
            await self.broadcast(log_message("WARNING", "Daemon restart requested", datetime.now().isoformat()))
            asyncio.create_task(self._restart_soon())
            return
        if message.type == MessageType.INVOKE_TOOL:
            await self._invoke_tool(websocket, message)
            return

        await websocket.send(error_message(f"Unknown command: {message.type}").to_json())

    async def _send_status(self, websocket: WebSocketServerProtocol) -> None:
        status = self.connection_manager.get_status()
        scene_state = self.session.get_scene_state()
        scene_data = scene_state.get("data", {}) if scene_state.get("success") else {}
        hip_file = scene_data.get("hip_file")
        if hip_file and isinstance(hip_file, str) and hip_file.lower() not in {"untitled", "unsaved"}:
            try:
                hip_file = os.path.abspath(hip_file)
            except Exception:
                pass
        await websocket.send(
            status_update(
                server_running=True,
                uptime_seconds=time.time() - self.start_time,
                houdini_connected=status["connected"],
                houdini_pid=status["pid"],
                backend_pid=os.getpid(),
                scene_node_count=scene_data.get("node_count"),
                hip_file=hip_file,
            ).to_json()
        )

    async def _send_process_count(self, websocket: WebSocketServerProtocol) -> None:
        hython_count = 0
        backend_count = 0
        for proc in psutil.process_iter(["name"]):
            try:
                if "hython" in (proc.info["name"] or "").lower():
                    hython_count += 1
                    if proc.pid == os.getpid():
                        backend_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        worker_count = max(hython_count - backend_count, 0)
        await websocket.send(
            process_count_message(
                hython_count,
                hython_count,
                backend_count=backend_count,
                worker_count=worker_count,
            ).to_json()
        )

    async def _restart_houdini(self) -> None:
        ok = self.connection_manager.restart()
        level = "INFO" if ok else "ERROR"
        text = "Houdini connection restarted" if ok else "Houdini connection restart failed"
        await self.broadcast(log_message(level, text, datetime.now().isoformat()))

    async def _invoke_tool(self, websocket: WebSocketServerProtocol, message: WSMessage) -> None:
        operation = message.data.get("operation", "")
        params = message.data.get("params", {})
        start_time = time.time()
        try:
            result = await self.session.execute(operation, params)
        except Exception as e:
            result = {"success": False, "error": str(e), "error_type": type(e).__name__}
        duration = result.get("_timing", {}).get("duration_seconds", time.time() - start_time)
        status = "success" if result.get("success") else "failed"

        flow_parts = [
            "FLOW",
            operation or "unknown",
            status,
            f"{duration:.2f}s",
        ]
        if params.get("input_path"):
            flow_parts.append(f"in={params.get('input_path')}")
        if params.get("geo_path"):
            flow_parts.append(f"in={params.get('geo_path')}")
        context = result.get("context") or result.get("data") or {}
        for key in ("output_path", "node_path", "hip_file"):
            value = context.get(key)
            if value and isinstance(value, str):
                flow_parts.append(f"out={value}")
                break
        if result.get("error"):
            flow_parts.append(f"error={result.get('error')}")
        logger.info(" | ".join(flow_parts))

        self.stats["total_operations"] += 1
        if result.get("success"):
            self.stats["successful_operations"] += 1
        else:
            self.stats["failed_operations"] += 1
        self.stats["operation_times"].append(duration)
        self.stats["operation_times"] = self.stats["operation_times"][-1000:]

        await websocket.send(
            WSMessage(MessageType.TOOL_RESULT, result, request_id=message.request_id).to_json()
        )

        await self.broadcast(
            operation_log(
                timestamp=datetime.now().isoformat(),
                operation=operation,
                status=status,
                duration=duration,
                params=params,
                result=result if result.get("success") else None,
                error=result.get("error"),
            )
        )

    async def broadcast(self, message: WSMessage) -> None:
        if not self.clients:
            return
        await asyncio.gather(
            *[client.send(message.to_json()) for client in list(self.clients)],
            return_exceptions=True,
        )

    def _write_state_files(self) -> None:
        payload = {
            "host": self.host,
            "port": self.port,
            "pid": os.getpid(),
            "timestamp": int(time.time()),
        }
        get_lock_file().write_text(f"pid={os.getpid()}\nstarted={asyncio.get_event_loop().time()}", encoding="utf-8")
        get_ws_port_instance_file().write_text(json.dumps(payload, indent=2), encoding="utf-8")
        get_ws_port_file().write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _cleanup_state_files(self) -> None:
        lock_file = get_lock_file()
        if lock_file.exists():
            try:
                lock_file.unlink()
            except Exception:
                pass

        instance_file = get_ws_port_instance_file()
        if instance_file.exists():
            try:
                instance_file.unlink()
            except Exception:
                pass

        latest_file = get_ws_port_file()
        if latest_file.exists():
            try:
                data = json.loads(latest_file.read_text(encoding="utf-8"))
            except Exception:
                data = {}
            if data.get("pid") == os.getpid():
                try:
                    latest_file.unlink()
                except Exception:
                    pass

    async def _shutdown_soon(self) -> None:
        await asyncio.sleep(0.5)
        await self.stop()
        os._exit(0)

    async def _restart_soon(self) -> None:
        await asyncio.sleep(0.5)
        python_exe = sys.executable
        os.execv(python_exe, [python_exe, "-m", "houdini_mcp.daemon_server"])


def _resolve_hython_path(houdini_bin_path: str | None) -> str:
    return resolve_hython_path(houdini_bin_path)


async def _run_daemon(args: argparse.Namespace) -> None:
    lock_file = get_lock_file()
    existing_pid = None
    if lock_file.exists():
        try:
            for line in lock_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("pid="):
                    existing_pid = int(line.split("=", 1)[1])
                    break
        except Exception:
            existing_pid = None

    if existing_pid and psutil.pid_exists(existing_pid) and existing_pid != os.getpid():
        logger.info(f"Daemon already running with PID {existing_pid}; exiting duplicate launcher")
        return

    if lock_file.exists() and (not existing_pid or not psutil.pid_exists(existing_pid)):
        try:
            lock_file.unlink()
        except Exception:
            pass

    hython_path = _resolve_hython_path(args.houdini_path)
    daemon = HoudiniDaemon(hython_path=hython_path, host="127.0.0.1", port=args.ws_port)
    await daemon.start()
    try:
        await asyncio.Future()
    finally:
        await daemon.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Persistent Houdini daemon")
    parser.add_argument("--houdini-path", default=None, help="Houdini bin path")
    parser.add_argument("--ws-port", type=int, default=9876, help="Daemon WebSocket port")
    args = parser.parse_args()
    asyncio.run(_run_daemon(args))


if __name__ == "__main__":
    main()
