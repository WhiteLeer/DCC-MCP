"""Client helpers for interactive Blender live bridge instances."""

from __future__ import annotations

import json
import socket
import time
from pathlib import Path
from typing import Any

import psutil


def get_live_state_dir() -> Path:
    return Path.home() / ".codex" / "mcp" / "blender-mcp" / "live"


def _read_instances() -> list[dict[str, Any]]:
    state_dir = get_live_state_dir()
    if not state_dir.exists():
        return []
    instances: list[dict[str, Any]] = []
    for path in state_dir.glob("live_*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            pid = int(data.get("pid", 0))
            if pid > 0 and psutil.pid_exists(pid):
                data["_state_file"] = str(path)
                instances.append(data)
            else:
                path.unlink(missing_ok=True)
        except Exception:
            continue
    return sorted(instances, key=lambda item: int(item.get("timestamp", 0)), reverse=True)


def _invoke(instance: dict[str, Any], operation: str, params: dict | None = None, timeout: float = 12.0) -> dict:
    payload = json.dumps({"operation": operation, "params": params or {}}, ensure_ascii=False) + "\n"
    with socket.create_connection((instance.get("host", "127.0.0.1"), int(instance["port"])), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(payload.encode("utf-8"))
        chunks: list[bytes] = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
    raw = b"".join(chunks).split(b"\n", 1)[0]
    return json.loads(raw.decode("utf-8"))


def invoke_live(operation: str, params: dict | None = None, blend_path: str = "") -> dict | None:
    instances = _read_instances()
    if blend_path:
        target = str(Path(blend_path).resolve()).lower()
        instances = [
            item for item in instances
            if item.get("blend_file") and str(Path(item["blend_file"]).resolve()).lower() == target
        ] + [
            item for item in instances
            if not item.get("blend_file") or str(Path(item.get("blend_file", "")).resolve()).lower() != target
        ]

    last_error: Exception | None = None
    for instance in instances:
        try:
            result = _invoke(instance, operation, params)
            instance["timestamp"] = int(time.time())
            return result
        except Exception as exc:
            last_error = exc
            try:
                Path(instance.get("_state_file", "")).unlink(missing_ok=True)
            except Exception:
                pass
            continue

    if last_error:
        return {"success": False, "error": str(last_error), "error_type": type(last_error).__name__}
    return None
