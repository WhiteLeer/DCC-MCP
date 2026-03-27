"""Launch helpers for DCC MCP GUI panels."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import psutil


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _pid_file() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    state_dir = codex_home / "mcp" / "dcc-mcp-gui"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "unified_gui_pid.json"


def _is_gui_running() -> bool:
    pid_path = _pid_file()
    if not pid_path.exists():
        return False
    try:
        data = json.loads(pid_path.read_text(encoding="utf-8"))
        pid = int(data.get("pid", 0))
    except Exception:
        return False
    if pid <= 0 or not psutil.pid_exists(pid):
        return False
    try:
        cmdline = " ".join(psutil.Process(pid).cmdline()).lower()
    except Exception:
        return False
    return "run_unified_gui.py" in cmdline


def ensure_unified_gui_running() -> bool:
    """Start unified GUI once, unless explicitly disabled."""
    if os.environ.get("DCC_MCP_AUTO_OPEN_GUI", "0").strip().lower() in {"0", "false", "no"}:
        return False
    if _is_gui_running():
        return True

    python_exe = sys.executable
    script = _repo_root() / "run_unified_gui.py"
    if not script.exists():
        return False

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    proc = subprocess.Popen(
        [python_exe, str(script)],
        cwd=str(_repo_root()),
        creationflags=creationflags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    _pid_file().write_text(
        json.dumps({"pid": proc.pid, "script": str(script)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return True
