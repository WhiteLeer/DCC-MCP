"""Daemon process management for the persistent Houdini backend."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import psutil

from houdini_mcp.utils.state_paths import (
    get_lock_file,
    get_state_dir,
    get_ws_port_file,
)
from houdini_mcp.utils.houdini_paths import resolve_hython_path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _daemon_python() -> str:
    override = os.environ.get("HOUDINI_MCP_DAEMON_PYTHON")
    if override:
        return override

    hython_path = resolve_hython_path()
    if Path(hython_path).exists():
        return hython_path

    current_name = Path(sys.executable).name.lower()
    if "python" in current_name or "hython" in current_name:
        return sys.executable

    python_on_path = shutil.which("python")
    if python_on_path:
        return python_on_path

    return sys.executable


def _read_live_pid() -> int | None:
    lock_file = get_lock_file()
    if not lock_file.exists():
        return None

    try:
        for line in lock_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("pid="):
                pid = int(line.split("=", 1)[1])
                if psutil.pid_exists(pid):
                    return pid
    except Exception:
        return None

    return None


def daemon_running() -> bool:
    return _read_live_pid() is not None


def cleanup_stale_state() -> None:
    state_dir = get_state_dir()
    live_pids = {proc.pid for proc in psutil.process_iter(["pid"])}

    for path in state_dir.glob("ws_port*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            pid = int(data.get("pid", 0))
        except Exception:
            pid = 0

        if pid <= 0 or pid not in live_pids:
            try:
                path.unlink()
            except Exception:
                pass

    lock_file = get_lock_file()
    if lock_file.exists() and _read_live_pid() is None:
        try:
            lock_file.unlink()
        except Exception:
            pass


def ensure_daemon_running(timeout_seconds: float = 10.0) -> bool:
    if daemon_running():
        return True

    cleanup_stale_state()

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    subprocess.Popen(
        [_daemon_python(), "-m", "houdini_mcp.daemon_server"],
        cwd=str(_repo_root()),
        creationflags=creationflags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if daemon_running() and get_ws_port_file().exists():
            return True
        time.sleep(0.25)

    return False
