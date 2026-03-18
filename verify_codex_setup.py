"""Verify Houdini MCP Codex setup and daemon state."""

from __future__ import annotations

import json
from pathlib import Path

import psutil


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def check_codex_config() -> bool:
    config_path = Path.home() / ".codex" / "config.toml"
    print_header("1. Codex config")
    print(f"Path: {config_path}")
    if not config_path.exists():
        print("FAIL: config.toml not found")
        return False

    text = config_path.read_text(encoding="utf-8", errors="ignore")
    ok = "[mcp_servers.houdini_mcp]" in text and "houdini_mcp/server_with_gui.py" in text
    print("OK: config.toml exists")
    print(f"Contains houdini_mcp entry: {ok}")
    return ok


def check_state_dir() -> bool:
    state_dir = Path.home() / ".codex" / "mcp" / "houdini-mcp"
    print_header("2. Runtime state")
    print(f"Path: {state_dir}")
    if not state_dir.exists():
        print("FAIL: state dir not found")
        return False

    files = sorted(p.name for p in state_dir.iterdir())
    print("Files:")
    for name in files:
        print(f"- {name}")

    port_file = state_dir / "ws_port.json"
    if not port_file.exists():
        print("FAIL: ws_port.json not found")
        return False

    data = json.loads(port_file.read_text(encoding="utf-8"))
    pid = int(data.get("pid", 0))
    alive = pid > 0 and psutil.pid_exists(pid)
    print(f"Active endpoint: ws://{data.get('host')}:{data.get('port')}")
    print(f"PID: {pid} alive={alive}")
    return alive


def check_processes() -> bool:
    print_header("3. Processes")
    found = False
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(proc.info.get("cmdline") or [])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

        if "houdini_mcp.daemon_server" in cmdline or "houdini_mcp/server_with_gui.py" in cmdline:
            found = True
            print(f"- PID {proc.info['pid']} {proc.info['name']}")
            print(f"  {cmdline}")

    if not found:
        print("FAIL: no daemon or bridge process found")
    return found


def check_logs() -> bool:
    print_header("4. Logs")
    ok = True
    for name in ["houdini-mcp-daemon", "houdini-mcp-bridge"]:
        log_dir = Path.home() / ".mcp_logs" / name
        print(f"{name}: {log_dir}")
        if not log_dir.exists():
            print("  FAIL: log dir missing")
            ok = False
            continue
        logs = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not logs:
            print("  FAIL: no log files")
            ok = False
            continue
        latest = logs[0]
        print(f"  Latest: {latest.name}")
    return ok


def main() -> None:
    results = [
        check_codex_config(),
        check_state_dir(),
        check_processes(),
        check_logs(),
    ]

    print_header("Summary")
    if all(results):
        print("OK: Codex setup looks healthy")
    else:
        print("WARN: Codex setup has issues; inspect the failed sections above")


if __name__ == "__main__":
    main()
