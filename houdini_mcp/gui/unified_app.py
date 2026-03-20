"""Unified DCC MCP control panel (Houdini/Maya/Blender/Substance)."""

from __future__ import annotations

import asyncio
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from qasync import QEventLoop

from .dcc_config import get_dcc_config
from .main_window import MainWindow


class UnifiedControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DCC MCP Unified Control Panel")
        self.setGeometry(80, 60, 1500, 920)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("DCC MCP 统一控制面板")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title)

        sub = QLabel("Houdini / Maya / Blender / Substance Designer")
        sub.setStyleSheet("color:#5c6b7a;")
        layout.addWidget(sub)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.child_panels: list[MainWindow] = []
        self._add_dcc_tab("houdini")
        self._add_dcc_tab("maya")
        self._add_dcc_tab("blender")
        self._add_dcc_tab("substance")

    def _add_dcc_tab(self, dcc_key: str) -> None:
        cfg = get_dcc_config(dcc_key)

        if cfg.ensure_daemon:
            try:
                cfg.ensure_daemon()
            except Exception:
                pass

        panel = MainWindow(
            dcc_name=cfg.display_name,
            state_dir_func=cfg.state_dir_func,
            app_title=f"{cfg.display_name} MCP 控制面板",
            log_dir_prefix=cfg.log_dir_prefix,
            supports_restart=cfg.supports_restart,
            port_range=cfg.port_range,
            strict_state=cfg.strict_state,
            ensure_daemon_func=cfg.ensure_daemon,
        )
        self.child_panels.append(panel)

        emoji = {
            "houdini": "🧰",
            "maya": "🎬",
            "blender": "🌀",
            "substance-designer": "🎨",
        }.get(cfg.key, "🧩")
        self.tabs.addTab(panel, f"{emoji} {cfg.display_name}")


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("DCC MCP Unified Control Panel")
    app.setOrganizationName("DCC MCP")

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = UnifiedControlPanel()
    screen_geo = app.primaryScreen().availableGeometry()
    window.setFixedSize(screen_geo.width(), screen_geo.height())
    window.move(screen_geo.left(), screen_geo.top())
    window.show()

    with loop:
        sys.exit(loop.run_forever())


if __name__ == "__main__":
    main()
