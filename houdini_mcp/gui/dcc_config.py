"""DCC configuration for shared GUI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from blender_mcp.utils.state_paths import get_state_dir as blender_state_dir
from houdini_mcp.utils.state_paths import get_state_dir as houdini_state_dir
from maya_mcp.utils.state_paths import get_state_dir as maya_state_dir


@dataclass(frozen=True)
class DccConfig:
    key: str
    display_name: str
    state_dir_func: Callable[[], Path]
    log_dir_prefix: str
    supports_restart: bool = False
    port_range: tuple[int, int] = (9876, 9885)
    strict_state: bool = True
    ensure_daemon: Callable[[], None] | None = None


def _codex_state_dir(subdir: str, env_override: str) -> Path:
    override = os.environ.get(env_override)
    if override:
        path = Path(override)
    else:
        codex_home = os.environ.get("CODEX_HOME")
        root = Path(codex_home) if codex_home else Path.home() / ".codex"
        path = root / "mcp" / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def _generic_state_dir(dcc_key: str) -> Path:
    return _codex_state_dir(f"{dcc_key}-mcp", f"{dcc_key.upper()}_MCP_STATE_DIR")


def get_dcc_config(dcc_key: str) -> DccConfig:
    key = dcc_key.lower()
    if key == "houdini":
        from houdini_mcp.daemon_launcher import ensure_daemon_running

        return DccConfig(
            key="houdini",
            display_name="Houdini",
            state_dir_func=houdini_state_dir,
            log_dir_prefix="houdini-mcp",
            supports_restart=True,
            port_range=(9876, 9885),
            strict_state=False,
            ensure_daemon=ensure_daemon_running,
        )

    if key == "maya":
        from maya_mcp.daemon_launcher import ensure_daemon_running

        return DccConfig(
            key="maya",
            display_name="Maya",
            state_dir_func=maya_state_dir,
            log_dir_prefix="maya-mcp",
            supports_restart=False,
            port_range=(9896, 9905),
            strict_state=True,
            ensure_daemon=ensure_daemon_running,
        )

    if key == "blender":
        from blender_mcp.daemon_launcher import ensure_daemon_running

        return DccConfig(
            key="blender",
            display_name="Blender",
            state_dir_func=blender_state_dir,
            log_dir_prefix="blender-mcp",
            supports_restart=False,
            port_range=(9910, 9919),
            strict_state=True,
            ensure_daemon=ensure_daemon_running,
        )

    if key in {"substance", "substance-designer", "substance_designer"}:
        from substance_mcp.daemon_launcher import ensure_daemon_running
        from substance_mcp.utils.state_paths import get_state_dir as substance_state_dir

        return DccConfig(
            key="substance-designer",
            display_name="Substance Designer",
            state_dir_func=substance_state_dir,
            log_dir_prefix="substance-designer-mcp",
            supports_restart=False,
            port_range=(9920, 9929),
            strict_state=True,
            ensure_daemon=ensure_daemon_running,
        )

        return DccConfig(
            key=key,
            display_name=key.title(),
            state_dir_func=lambda: _generic_state_dir(key),
            log_dir_prefix=f"{key}-mcp",
            supports_restart=False,
            port_range=(9930, 9939),
            strict_state=True,
            ensure_daemon=None,
        )
