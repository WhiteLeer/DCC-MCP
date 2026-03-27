"""Unified DCC MCP control panel (Houdini/Maya/Blender/Substance)."""

from __future__ import annotations

import asyncio
import json
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QFrame,
)
from qasync import QEventLoop
import websockets

from .dcc_config import get_dcc_config
from .unified_state import load_enabled_modules, save_enabled_modules
from .widgets.logs_widget import LogsWidget
from .widgets.module_list_widget import ModuleListWidget


class UnifiedControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DCC MCP Unified Control Panel")
        self.setGeometry(80, 60, 760, 900)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        root.setStyleSheet("QWidget { background:#f6f7fb; color:#1f2933; }")

        title = QLabel("可选模块:")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title)

        module_frame = QFrame()
        module_frame.setStyleSheet(
            "QFrame { background:#ffffff; border:1px solid #d6dde6; border-radius:10px; }"
        )
        module_layout = QVBoxLayout(module_frame)
        module_layout.setContentsMargins(8, 8, 8, 8)
        module_layout.setSpacing(6)

        configs = [
            get_dcc_config("houdini"),
            get_dcc_config("blender"),
            get_dcc_config("maya"),
            get_dcc_config("substance"),
        ]
        default_enabled = {cfg.key: True for cfg in configs}
        enabled = load_enabled_modules(default_enabled)

        self._configs = {cfg.key: cfg for cfg in configs}
        self.module_list = ModuleListWidget(configs, enabled)
        self.module_list.toggled.connect(self._on_modules_toggled)
        self.module_list.module_toggled.connect(self._on_module_toggled)
        module_layout.addWidget(self.module_list)
        layout.addWidget(module_frame)

        logs_title = QLabel("调用日志:")
        logs_title.setFont(title_font)
        layout.addWidget(logs_title)

        self.logs = LogsWidget(
            log_dir_prefixes=self._enabled_prefixes(enabled),
            compact=True,
        )
        layout.addWidget(self.logs, 1)

        self._ensure_enabled_daemons(configs, enabled)
        self.logs.load_recent_logs()

        self._heartbeat_timer = QTimer()
        self._heartbeat_timer.timeout.connect(self._schedule_status_refresh)
        self._heartbeat_timer.start(3000)
        self._schedule_status_refresh()

    def _enabled_prefixes(self, enabled: dict[str, bool]) -> list[str]:
        prefixes = []
        if enabled.get("houdini"):
            prefixes.append("houdini-mcp")
        if enabled.get("maya"):
            prefixes.append("maya-mcp")
        if enabled.get("blender"):
            prefixes.append("blender-mcp")
        if enabled.get("substance-designer"):
            prefixes.append("substance-designer-mcp")
        return prefixes

    def _ensure_enabled_daemons(self, configs: list, enabled: dict[str, bool]) -> None:
        for cfg in configs:
            if not enabled.get(cfg.key, True):
                continue
            if cfg.ensure_daemon:
                try:
                    cfg.ensure_daemon()
                except Exception:
                    pass

    def _on_modules_toggled(self, enabled: dict[str, bool]) -> None:
        save_enabled_modules(enabled)
        self.logs.set_log_prefixes(self._enabled_prefixes(enabled))
        self.logs.load_recent_logs()

    def _on_module_toggled(self, key: str, enabled: bool) -> None:
        cfg = self._configs.get(key)
        if not cfg:
            return
        if enabled:
            if cfg.ensure_daemon:
                try:
                    cfg.ensure_daemon()
                except Exception:
                    pass
            self._schedule_status_refresh()
        else:
            try:
                asyncio.get_running_loop().create_task(self._shutdown_daemon(cfg))
            except RuntimeError:
                asyncio.get_event_loop().create_task(self._shutdown_daemon(cfg))

    def _schedule_status_refresh(self) -> None:
        try:
            asyncio.get_running_loop().create_task(self._refresh_statuses())
        except RuntimeError:
            asyncio.get_event_loop().create_task(self._refresh_statuses())

    def _get_ws_url(self, cfg) -> str | None:
        state_dir = cfg.state_dir_func()
        ws_file = state_dir / "ws_port.json"
        if not ws_file.exists():
            return None
        try:
            payload = json.loads(ws_file.read_text(encoding="utf-8"))
            host = payload.get("host", "127.0.0.1")
            port = int(payload.get("port", 0))
        except Exception:
            return None
        if port <= 0:
            return None
        return f"ws://{host}:{port}"

    async def _ping_status(self, url: str) -> bool:
        try:
            async with websockets.connect(url, ping_interval=None, close_timeout=0.2) as ws:
                await ws.send(json.dumps({"type": "get_status", "data": {}}))
                raw = await asyncio.wait_for(ws.recv(), timeout=0.6)
            msg = json.loads(raw)
            return msg.get("type") == "status_update"
        except Exception:
            return False

    async def _refresh_statuses(self) -> None:
        enabled = self.module_list.enabled_modules()
        status_map: dict[str, str] = {}
        for key, cfg in self._configs.items():
            if not enabled.get(key, True):
                status_map[key] = "关闭"
                continue
            url = self._get_ws_url(cfg)
            if not url:
                status_map[key] = "未启动"
                continue
            ok = await self._ping_status(url)
            status_map[key] = "运行中" if ok else "未响应"
        self.module_list.update_status_map(status_map)

    async def _shutdown_daemon(self, cfg) -> None:
        url = self._get_ws_url(cfg)
        if not url:
            return
        try:
            async with websockets.connect(url, ping_interval=None, close_timeout=0.2) as ws:
                await ws.send(json.dumps({"type": "shutdown", "data": {}}))
        except Exception:
            pass
        self._schedule_status_refresh()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("DCC MCP Unified Control Panel")
    app.setOrganizationName("DCC MCP")

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = UnifiedControlPanel()
    window.show()

    with loop:
        sys.exit(loop.run_forever())


if __name__ == "__main__":
    main()
