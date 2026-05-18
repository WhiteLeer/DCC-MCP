"""Daemon process management for the Maya backend."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from dcc_mcp_common.daemon_launcher import ensure_daemon_running as _ensure_daemon_running

from maya_mcp.utils.state_paths import get_lock_file, get_state_dir, get_ws_port_file


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _daemon_python() -> str:
    override = os.environ.get("MAYA_MCP_DAEMON_PYTHON")
    if override:
        return override

    maya_bin = os.environ.get("MAYA_BIN")
    if maya_bin:
        mayapy = Path(maya_bin) / "mayapy.exe"
        if mayapy.exists():
            return str(mayapy)

    default_mayapy = Path("C:/Program Files/Autodesk/Maya2026/bin/mayapy.exe")
    if default_mayapy.exists():
        return str(default_mayapy)

    current_name = Path(sys.executable).name.lower()
    if "python" in current_name or "mayapy" in current_name:
        return sys.executable

    python_on_path = shutil.which("python")
    if python_on_path:
        return python_on_path

    return sys.executable


def ensure_daemon_running(timeout_seconds: float = 10.0) -> bool:
    return _ensure_daemon_running(
        lock_file=get_lock_file(),
        state_dir=get_state_dir(),
        ws_port_file=get_ws_port_file(),
        daemon_module="maya_mcp.daemon_server",
        daemon_python=_daemon_python(),
        repo_root=_repo_root(),
        timeout_seconds=timeout_seconds,
    )
