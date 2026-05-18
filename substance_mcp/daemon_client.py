"""Client for the persistent Substance Designer daemon."""

from __future__ import annotations

from dcc_mcp_common.daemon_client import invoke_via_daemon

from substance_mcp.daemon_launcher import ensure_daemon_running
from substance_mcp.utils.state_paths import get_state_dir


async def invoke_operation(operation: str, params: dict) -> dict:
    return await invoke_via_daemon(
        ensure_running=ensure_daemon_running,
        state_dir=get_state_dir(),
        fallback_ports=range(9920, 9930),
        operation=operation,
        params=params,
        recv_timeout=60,
    )
