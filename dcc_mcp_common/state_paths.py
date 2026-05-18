"""Shared runtime state path helpers for DCC MCP backends."""

from __future__ import annotations

import os
from pathlib import Path


def get_codex_home() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home)
    return Path.home() / ".codex"


def get_state_dir(app_slug: str, env_var: str | None = None) -> Path:
    override = os.environ.get(env_var) if env_var else None
    path = Path(override) if override else get_codex_home() / "mcp" / app_slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_ws_port_file(state_dir: Path) -> Path:
    return state_dir / "ws_port.json"


def get_ws_port_instance_file(state_dir: Path, pid: int | None = None) -> Path:
    if pid is None:
        pid = os.getpid()
    return state_dir / f"ws_port_{pid}.json"


def get_lock_file(state_dir: Path) -> Path:
    return state_dir / ".running.lock"
