"""Persistent Substance Designer daemon for GUI control and MCP bridging."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional, Set

import psutil
import websockets
from websockets.server import WebSocketServerProtocol

from substance_mcp.substance_session import SubstanceSessionBackend
from substance_mcp.utils.state_paths import (
    get_lock_file,
    get_ws_port_file,
    get_ws_port_instance_file,
)
from houdini_mcp.utils.logging_config import setup_logging
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
    name="substance-designer-mcp-daemon",
    log_level="INFO",
    enable_file_logging=True,
    enable_console_logging=True,
)


class SubstanceDaemon:
    def __init__(self, designer_exe: str | None, host: str = "127.0.0.1", port: int = 9920):
        self.host = host
        self.port = port
        self.session = SubstanceSessionBackend(designer_exe)
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server: Optional[websockets.WebSocketServer] = None
        self.start_time = time.time()

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
        logger.info(f"Substance daemon listening on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        self._cleanup_state_files()

    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str | None = None) -> None:
        client_addr = websocket.remote_address
        logger.info(f"Client connected: {client_addr}")
        self.clients.add(websocket)
        try:
            await self._send_status(websocket)
            async for message in websocket:
                await self._handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_addr}")
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
        scene_state = self.session.get_scene_state()
        scene_data = scene_state.get("data", {}) if scene_state.get("success") else {}
        await websocket.send(
            status_update(
                server_running=True,
                uptime_seconds=time.time() - self.start_time,
                houdini_connected=True,
                houdini_pid=os.getpid(),
                backend_pid=os.getpid(),
                scene_node_count=scene_data.get("designer_process_count", 0),
                hip_file=scene_data.get("scene_path", "untitled"),
            ).to_json()
        )

    async def _send_process_count(self, websocket: WebSocketServerProtocol) -> None:
        process_count = 0
        backend_count = 0
        for proc in psutil.process_iter(["name"]):
            try:
                name = (proc.info["name"] or "").lower()
                if "python" in name and proc.pid == os.getpid():
                    backend_count += 1
                if "substance 3d designer" in name:
                    process_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        await websocket.send(
            process_count_message(
                process_count,
                process_count,
                backend_count=backend_count,
                worker_count=max(process_count - backend_count, 0),
            ).to_json()
        )

    async def _invoke_tool(self, websocket: WebSocketServerProtocol, message: WSMessage) -> None:
        operation = message.data.get("operation", "")
        params = message.data.get("params", {})
        start_time = time.time()
        try:
            result = await self.session.execute(operation, params)
        except Exception as e:
            result = {"success": False, "error": str(e), "error_type": type(e).__name__}
        duration = time.time() - start_time

        await websocket.send(
            WSMessage(MessageType.TOOL_RESULT, result, request_id=message.request_id).to_json()
        )
        await self.broadcast(
            operation_log(
                timestamp=datetime.now().isoformat(),
                operation=operation,
                status="success" if result.get("success") else "failed",
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
        os.execv(python_exe, [python_exe, "-m", "substance_mcp.daemon_server"])


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

    daemon = SubstanceDaemon(designer_exe=args.designer_exe, host="127.0.0.1", port=args.ws_port)
    await daemon.start()
    try:
        await asyncio.Future()
    finally:
        await daemon.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Persistent Substance Designer daemon")
    parser.add_argument("--designer-exe", default=os.environ.get("SUBSTANCE_DESIGNER_EXE"), help="Substance Designer executable path")
    parser.add_argument("--ws-port", type=int, default=9920, help="Daemon WebSocket port")
    args = parser.parse_args()
    asyncio.run(_run_daemon(args))


if __name__ == "__main__":
    main()

