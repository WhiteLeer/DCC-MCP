"""Shared daemon client helpers."""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

import psutil
import websockets

from houdini_mcp.websocket_protocol import MessageType, WSMessage


def candidate_urls(state_dir: Path, fallback_ports: range) -> list[str]:
    urls: list[str] = []
    entries: list[tuple[int, str]] = []

    for path in state_dir.glob("ws_port*.json"):
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

    for port in fallback_ports:
        url = f"ws://127.0.0.1:{port}"
        if url not in urls:
            urls.append(url)

    return urls


async def invoke_via_daemon(
    *,
    ensure_running,
    restart_running=None,
    state_dir: Path,
    fallback_ports: range,
    operation: str,
    params: dict,
    recv_timeout: float,
) -> dict:
    request_id = str(uuid.uuid4())
    payload = WSMessage(
        MessageType.INVOKE_TOOL,
        {"operation": operation, "params": params},
        request_id=request_id,
    ).to_json()

    async def _try_invoke() -> tuple[dict | None, Exception | None]:
        last_error: Exception | None = None
        for url in candidate_urls(state_dir, fallback_ports):
            try:
                async with websockets.connect(url, open_timeout=3) as ws:
                    await ws.send(payload)
                    while True:
                        raw = await asyncio.wait_for(ws.recv(), timeout=recv_timeout)
                        message = json.loads(raw)
                        if message.get("type") == MessageType.TOOL_RESULT.value and message.get("request_id") == request_id:
                            return message.get("data", {}), None
            except Exception as e:
                last_error = e
                continue
        return None, last_error

    if not ensure_running():
        return {"success": False, "error": "Daemon failed to start", "error_type": "DaemonStartError"}

    result, last_error = await _try_invoke()
    if result is not None:
        return result

    # Single-shot self-healing path for stale lock/socket state.
    if restart_running is not None and restart_running():
        result, last_error = await _try_invoke()
        if result is not None:
            return result

    return {
        "success": False,
        "error": str(last_error) if last_error else "Unable to reach daemon",
        "error_type": "DaemonConnectionError",
    }
