"""Shared daemon process launch helpers."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Callable

import psutil


def read_live_pid(lock_file: Path) -> int | None:
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


def cleanup_stale_state(state_dir: Path, lock_file: Path) -> None:
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

    if lock_file.exists() and read_live_pid(lock_file) is None:
        try:
            lock_file.unlink()
        except Exception:
            pass


def ensure_daemon_running(
    *,
    lock_file: Path,
    state_dir: Path,
    ws_port_file: Path,
    daemon_module: str,
    daemon_python: str,
    repo_root: Path,
    extra_args: list[str] | None = None,
    timeout_seconds: float = 10.0,
    force_restart: bool = False,
    pid_exists: Callable[[int], bool] | None = None,
) -> bool:
    pid_exists = pid_exists or psutil.pid_exists

    live_pid = read_live_pid(lock_file)
    if live_pid is not None:
        if not force_restart:
            return True
        try:
            proc = psutil.Process(live_pid)
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()
        except Exception:
            pass

    cleanup_stale_state(state_dir, lock_file)

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    cmd = [daemon_python, "-m", daemon_module]
    if extra_args:
        cmd.extend(extra_args)

    subprocess.Popen(
        cmd,
        cwd=str(repo_root),
        creationflags=creationflags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        live_pid = read_live_pid(lock_file)
        if live_pid is not None and pid_exists(live_pid) and ws_port_file.exists():
            return True
        time.sleep(0.25)

    return False
