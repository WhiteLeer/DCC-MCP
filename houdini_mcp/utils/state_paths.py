"""Shared state paths for Houdini MCP (Codex-first)."""

from __future__ import annotations

import os
from pathlib import Path


def _get_codex_home() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home)
    return Path.home() / ".codex"


def get_state_dir() -> Path:
    """Return the directory for runtime state files."""
    override = os.environ.get("HOUDINI_MCP_STATE_DIR")
    if override:
        path = Path(override)
    else:
        path = _get_codex_home() / "mcp" / "houdini-mcp"

    path.mkdir(parents=True, exist_ok=True)
    return path


def get_ws_port_file() -> Path:
    """Return the latest WebSocket port file path."""
    return get_state_dir() / "ws_port.json"


def get_ws_port_instance_file(pid: int | None = None) -> Path:
    """Return the per-process WebSocket port file path."""
    if pid is None:
        pid = os.getpid()
    return get_state_dir() / f"ws_port_{pid}.json"


def get_lock_file() -> Path:
    """Return the lock file path used to prevent multiple instances."""
    return get_state_dir() / ".running.lock"
