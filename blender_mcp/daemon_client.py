"""Client for the persistent Blender daemon."""

from __future__ import annotations

from dcc_mcp_common.daemon_client import invoke_via_daemon

from blender_mcp.daemon_launcher import ensure_daemon_running, restart_daemon
from blender_mcp.utils.state_paths import get_state_dir


async def invoke_operation(operation: str, params: dict) -> dict:
    return await invoke_via_daemon(
        ensure_running=ensure_daemon_running,
        restart_running=restart_daemon,
        state_dir=get_state_dir(),
        fallback_ports=range(9910, 9920),
        operation=operation,
        params=params,
        recv_timeout=120,
    )
