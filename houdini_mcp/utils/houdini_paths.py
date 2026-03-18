"""Helpers for locating Houdini executables."""

from __future__ import annotations

import os
from pathlib import Path


DEFAULT_HOUDINI_BIN = Path("C:/Program Files/Side Effects Software/Houdini 20.5.487/bin")


def resolve_houdini_bin_path(houdini_bin_path: str | None = None) -> Path:
    if houdini_bin_path:
        return Path(houdini_bin_path)

    env_path = os.environ.get("HOUDINI_PATH")
    if env_path:
        path = Path(env_path)
        if path.name.lower() == "bin":
            return path

    return DEFAULT_HOUDINI_BIN


def resolve_hython_path(houdini_bin_path: str | None = None) -> str:
    return str(resolve_houdini_bin_path(houdini_bin_path) / "hython.exe")
