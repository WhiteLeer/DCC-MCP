"""Client for the persistent Substance Designer daemon."""

from __future__ import annotations

import asyncio
import json
import uuid

import psutil
import websockets

from substance_mcp.daemon_launcher import ensure_daemon_running
from substance_mcp.utils.state_paths import get_state_dir
from houdini_mcp.websocket_protocol import MessageType, WSMessage


def _candidate_urls() -> list[str]:
    urls: list[str] = []
    entries: list[tuple[int, str]] = []

    for path in get_state_dir().glob("ws_port*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            pid = int(data.get("pid", 0))
            timestamp = int(data.get("timestamp", 0))
            if pid > 0 and psutil.pid_exists(pid):
                entries.append((timestamp, f"ws://{data['host']}:{int(data['port'])}"))
        except Exception:
            continue

    for _, url in sorted(entries, key=lambda item: item[0], reverse=True):
        if url not in urls:
            urls.append(url)

    for port in range(9920, 9930):
        url = f"ws://127.0.0.1:{port}"
        if url not in urls:
            urls.append(url)

    return urls


async def invoke_operation(operation: str, params: dict) -> dict:
    if not ensure_daemon_running():
        return {"success": False, "error": "Daemon failed to start", "error_type": "DaemonStartError"}

    request_id = str(uuid.uuid4())
    payload = WSMessage(
        MessageType.INVOKE_TOOL,
        {"operation": operation, "params": params},
        request_id=request_id,
    ).to_json()

    last_error: Exception | None = None

    for url in _candidate_urls():
        try:
            async with websockets.connect(url, open_timeout=3) as ws:
                await ws.send(payload)
                while True:
                    raw = await asyncio.wait_for(ws.recv(), timeout=60)
                    message = json.loads(raw)
                    if message.get("type") == MessageType.TOOL_RESULT.value and message.get("request_id") == request_id:
                        return message.get("data", {})
        except Exception as e:
            last_error = e
            continue

    return {
        "success": False,
        "error": str(last_error) if last_error else "Unable to reach daemon",
        "error_type": "DaemonConnectionError",
    }

