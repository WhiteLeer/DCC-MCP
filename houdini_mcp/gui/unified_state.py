"""State helpers for the unified control panel."""

from __future__ import annotations

import json
import os
from pathlib import Path


def _state_dir() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    root = Path(codex_home) if codex_home else Path.home() / ".codex"
    path = root / "mcp" / "dcc-mcp-gui"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_state_file() -> Path:
    return _state_dir() / "unified_gui_state.json"


def load_enabled_modules(defaults: dict[str, bool]) -> dict[str, bool]:
    path = get_state_file()
    if not path.exists():
        return defaults.copy()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return defaults.copy()

    enabled = payload.get("enabled")
    if not isinstance(enabled, dict):
        return defaults.copy()

    merged = defaults.copy()
    for key, value in enabled.items():
        if key in merged:
            merged[key] = bool(value)
    return merged


def save_enabled_modules(enabled: dict[str, bool]) -> None:
    path = get_state_file()
    payload = {"enabled": enabled}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
