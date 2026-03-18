"""WebSocket server for GUI control."""

import asyncio
import logging
import time
import os
import sys
import psutil
from typing import Set, Optional, Dict, Any
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol

from .websocket_protocol import (
    WSMessage, MessageType,
    status_update, log_message, error_message, process_count_message
)
from .connection_manager import HoudiniConnectionManager

# Use the configured logger from server
logger = logging.getLogger("houdini-mcp-gui")


class WebSocketControlServer:
    """WebSocket server for MCP GUI control.

    Listens on localhost (default port 9876) and handles commands from GUI.
    """

    def __init__(
        self,
        connection_manager: HoudiniConnectionManager,
        host: str = "127.0.0.1",
        port: int = 9876
    ):
        self.host = host
        self.port = port
        self.connection_manager = connection_manager
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server: Optional[websockets.WebSocketServer] = None
        self.start_time = time.time()

        # Operation statistics
        self.stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "operation_times": []
        }

    async def start(self):
        """Start WebSocket server with auto port fallback."""
        original_port = self.port
        max_attempts = 10

        for attempt in range(max_attempts):
            try:
                self.server = await websockets.serve(
                    self._handle_client,
                    self.host,
                    self.port
                )

                if self.port != original_port:
                    logger.warning(f"⚠️ Port {original_port} was occupied, using {self.port} instead")

                logger.info(f"✅ WebSocket server started on ws://{self.host}:{self.port}")
                return

            except (OSError, RuntimeError) as e:
                # Check if it's a port binding error
                error_str = str(e).lower()
                is_port_error = (
                    "address already in use" in error_str or
                    "10048" in error_str or
                    "只允许使用一次" in error_str or  # Chinese error message
                    "bind" in error_str
                )

                if is_port_error:
                    # Port occupied, try next available port
                    old_port = self.port
                    self.port = self._find_free_port(self.port + 1)
                    logger.info(f"⚠️ Port {old_port} occupied, auto-switched to port {self.port}")
                else:
                    # Other error, re-raise
                    logger.error(f"❌ Failed to start WebSocket server: {e}")
                    raise
            except Exception as e:
                logger.error(f"❌ Failed to start WebSocket server: {e}")
                raise

        # If we exhausted all attempts
        raise RuntimeError(f"Could not find available port after {max_attempts} attempts (tried {original_port}-{self.port})")

    def _find_free_port(self, start_port: int = 9876) -> int:
        """Find a free port starting from start_port."""
        import socket

        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, port))
                    return port
            except OSError:
                continue

        # Fallback: let OS choose
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, 0))
            return s.getsockname()[1]

    async def stop(self):
        """Stop WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")

    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str | None = None):
        """Handle new client connection."""
        client_addr = websocket.remote_address
        logger.info(f"📱 GUI client connected: {client_addr}")
        self.clients.add(websocket)

        try:
            # Send initial status
            await self._send_status(websocket)

            # Handle messages
            async for message in websocket:
                await self._handle_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"📱 GUI client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"❌ Error handling client {client_addr}: {e}", exc_info=True)
        finally:
            self.clients.remove(websocket)

    async def _handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming message from GUI."""
        try:
            msg = WSMessage.from_json(message)
            logger.debug(f"📨 Received command: {msg.type}")

            # Dispatch command
            if msg.type == MessageType.RESTART_HOUDINI:
                await self._handle_restart(websocket)

            elif msg.type == MessageType.RESTART_MCP_SERVER:
                await self._handle_restart_mcp_server(websocket)

            elif msg.type == MessageType.GET_PROCESS_COUNT:
                await self._handle_get_process_count(websocket)

            elif msg.type == MessageType.RELOAD_CONFIG:
                await self._handle_reload_config(websocket, msg.data)

            elif msg.type == MessageType.CLEAR_CACHE:
                await self._handle_clear_cache(websocket)

            elif msg.type == MessageType.UPDATE_TIMEOUT:
                await self._handle_update_timeout(websocket, msg.data)

            elif msg.type == MessageType.GET_STATUS:
                await self._send_status(websocket)

            elif msg.type == MessageType.SHUTDOWN:
                await self._handle_shutdown(websocket)

            else:
                logger.warning(f"⚠️ Unknown command: {msg.type}")
                response = error_message(f"Unknown command: {msg.type}")
                await websocket.send(response.to_json())

        except Exception as e:
            logger.error(f"❌ Error handling message: {e}", exc_info=True)
            response = error_message(str(e))
            await websocket.send(response.to_json())

    async def _handle_restart(self, websocket: WebSocketServerProtocol):
        """Handle restart_houdini command."""
        logger.info("🔄 Restarting Houdini connection...")

        # Send log message
        msg = log_message(
            "INFO",
            "Restarting Houdini connection...",
            datetime.now().isoformat()
        )
        await self.broadcast(msg)

        # Perform restart
        success = self.connection_manager.restart()

        # Send result
        if success:
            msg = log_message(
                "INFO",
                "✅ Houdini connection restarted successfully",
                datetime.now().isoformat()
            )
        else:
            msg = log_message(
                "ERROR",
                "❌ Failed to restart Houdini connection",
                datetime.now().isoformat()
            )

        await self.broadcast(msg)
        await self._send_status(websocket)

    async def _handle_reload_config(self, websocket: WebSocketServerProtocol, config: Dict[str, Any]):
        """Handle reload_config command."""
        logger.info(f"⚙️ Reloading config: {config}")

        msg = log_message(
            "INFO",
            f"Reloading configuration...",
            datetime.now().isoformat()
        )
        await self.broadcast(msg)

        try:
            self.connection_manager.reload_config(config)

            msg = log_message(
                "INFO",
                "✅ Configuration reloaded successfully",
                datetime.now().isoformat()
            )
            await self.broadcast(msg)

        except Exception as e:
            logger.error(f"❌ Failed to reload config: {e}")
            msg = error_message(f"Failed to reload config: {e}")
            await websocket.send(msg.to_json())

    async def _handle_clear_cache(self, websocket: WebSocketServerProtocol):
        """Handle clear_cache command."""
        logger.info("🧹 Clearing cache...")

        msg = log_message(
            "INFO",
            "Clearing cache...",
            datetime.now().isoformat()
        )
        await self.broadcast(msg)

        self.connection_manager.clear_cache()

        msg = log_message(
            "INFO",
            "✅ Cache cleared",
            datetime.now().isoformat()
        )
        await self.broadcast(msg)

    async def _handle_update_timeout(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle update_timeout command."""
        operation = data.get("operation")
        timeout = data.get("timeout")

        logger.info(f"⏱️ Updating timeout for {operation}: {timeout}s")

        msg = log_message(
            "INFO",
            f"Updated timeout for {operation}: {timeout}s",
            datetime.now().isoformat()
        )
        await self.broadcast(msg)

    async def _handle_restart_mcp_server(self, websocket: WebSocketServerProtocol):
        """Handle restart_mcp_server command - exit process to let Codex restart."""
        logger.info("🔄 MCP Server restart requested from GUI")

        msg = log_message(
            "WARNING",
            "🔄 Restarting MCP Server... Codex will automatically restart the process.",
            datetime.now().isoformat()
        )
        await self.broadcast(msg)

        # Give clients time to receive the message
        await asyncio.sleep(0.5)

        # Exit current process - Codex will automatically restart it
        logger.info("🛑 Exiting for restart...")
        os._exit(0)

    async def _handle_get_process_count(self, websocket: WebSocketServerProtocol):
        """Handle get_process_count command - count hython processes."""
        try:
            hython_count = 0
            current_pid = os.getpid()

            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if 'hython' in proc_name:
                        hython_count += 1
                        pid = proc.info['pid']
                        is_current = " (current)" if pid == current_pid else ""
                        logger.debug(f"  Found hython process: PID={pid}{is_current}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            logger.info(f"📊 Process count: {hython_count} hython process(es)")

            # Send response
            msg = process_count_message(hython_count, hython_count)
            await websocket.send(msg.to_json())

        except Exception as e:
            logger.error(f"❌ Failed to get process count: {e}")
            response = error_message(f"Failed to get process count: {e}")
            await websocket.send(response.to_json())

    async def _handle_shutdown(self, websocket: WebSocketServerProtocol):
        """Handle shutdown command."""
        logger.info("🛑 Shutdown requested from GUI")

        msg = log_message(
            "WARNING",
            "Server shutdown requested",
            datetime.now().isoformat()
        )
        await self.broadcast(msg)

        # Note: Actual shutdown should be handled by main server

    async def _send_status(self, websocket: WebSocketServerProtocol):
        """Send current status to client."""
        status = self.connection_manager.get_status()

        msg = status_update(
            server_running=True,
            uptime_seconds=time.time() - self.start_time,
            houdini_connected=status["connected"],
            houdini_pid=status["pid"]
        )

        await websocket.send(msg.to_json())

    async def broadcast(self, message: WSMessage):
        """Broadcast message to all connected clients."""
        if not self.clients:
            return

        # Send to all clients concurrently
        await asyncio.gather(
            *[client.send(message.to_json()) for client in self.clients],
            return_exceptions=True
        )

    def log_operation(
        self,
        operation: str,
        status: str,
        duration: float,
        params: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Log operation and broadcast to clients.

        Called by MCP server after each operation.
        """
        # Update statistics
        self.stats["total_operations"] += 1
        if status == "success":
            self.stats["successful_operations"] += 1
        else:
            self.stats["failed_operations"] += 1

        self.stats["operation_times"].append(duration)

        # Keep only last 1000 operation times
        if len(self.stats["operation_times"]) > 1000:
            self.stats["operation_times"] = self.stats["operation_times"][-1000:]

        # Create message (but don't await - we're not in async context)
        # Store for periodic broadcast
        logger.debug(f"📊 Operation logged: {operation} ({status}) - {duration:.2f}s")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics."""
        times = self.stats["operation_times"]

        if not times:
            return {
                "total_operations": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "p95_response_time": 0.0,
                "p99_response_time": 0.0
            }

        sorted_times = sorted(times)
        n = len(sorted_times)

        return {
            "total_operations": self.stats["total_operations"],
            "success_rate": (
                self.stats["successful_operations"] / self.stats["total_operations"]
                if self.stats["total_operations"] > 0 else 0.0
            ),
            "avg_response_time": sum(sorted_times) / n,
            "p95_response_time": sorted_times[int(n * 0.95)] if n > 0 else 0.0,
            "p99_response_time": sorted_times[int(n * 0.99)] if n > 0 else 0.0
        }
