"""Shared state paths for Substance Designer MCP (Codex-first)."""

from __future__ import annotations

from pathlib import Path

from dcc_mcp_common import state_paths as common


_APP_SLUG = "substance-designer-mcp"
_ENV_VAR = "SUBSTANCE_DESIGNER_MCP_STATE_DIR"


def get_state_dir() -> Path:
    return common.get_state_dir(_APP_SLUG, _ENV_VAR)


def get_ws_port_file() -> Path:
    return common.get_ws_port_file(get_state_dir())


def get_ws_port_instance_file(pid: int | None = None) -> Path:
    return common.get_ws_port_instance_file(get_state_dir(), pid)


def get_lock_file() -> Path:
    return common.get_lock_file(get_state_dir())
