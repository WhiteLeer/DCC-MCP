"""Module list widget for unified control panel."""

from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QFrame,
    QPushButton,
)

from ..dcc_config import DccConfig


class ModuleListWidget(QWidget):
    """Selectable DCC modules list."""

    toggled = pyqtSignal(dict)
    module_toggled = pyqtSignal(str, bool)

    def __init__(self, configs: list[DccConfig], enabled: dict[str, bool]):
        super().__init__()
        self._configs = configs
        self._enabled = enabled.copy()
        self._checkboxes: dict[str, QCheckBox] = {}
        self._status_labels: dict[str, QLabel] = {}
        self._path_labels: dict[str, QLabel] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        for cfg in self._configs:
            row = self._build_row(cfg)
            layout.addWidget(row)

        hint = QLabel("可拓展…")
        hint.setStyleSheet("color:#7a7a7a;")
        layout.addWidget(hint)

        layout.addStretch()

    def _build_row(self, cfg: DccConfig) -> QWidget:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet(
            "QFrame { background:#f9fafb; border:1px solid #e2e8f0; border-radius:8px; }"
        )
        row = QHBoxLayout(frame)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(10)

        checkbox = QCheckBox(cfg.display_name)
        checkbox.setChecked(self._enabled.get(cfg.key, True))
        checkbox.setStyleSheet("QCheckBox { color: #1f2933; }")
        checkbox.stateChanged.connect(lambda _state, key=cfg.key: self._on_toggle(key))
        self._checkboxes[cfg.key] = checkbox
        row.addWidget(checkbox)

        path_label = QLabel(self._format_path(cfg.key))
        path_label.setStyleSheet("color:#4b5563;")
        path_font = QFont("Consolas", 9)
        path_label.setFont(path_font)
        path_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._path_labels[cfg.key] = path_label
        row.addWidget(path_label, 1)

        status = QLabel(self._status_text(cfg))
        status.setStyleSheet("color:#9ad18b;")
        self._status_labels[cfg.key] = status
        row.addWidget(status)

        open_btn = QPushButton("打开")
        open_btn.setFixedWidth(52)
        open_btn.clicked.connect(lambda _state, key=cfg.key: self._open_exe(key))
        row.addWidget(open_btn)

        path_btn = QPushButton("路径")
        path_btn.setFixedWidth(52)
        path_btn.clicked.connect(lambda _state, key=cfg.key: self._open_folder(key))
        row.addWidget(path_btn)

        return frame

    def _format_path(self, key: str) -> str:
        exe = ""
        if key == "houdini":
            exe = os.environ.get("HOUDINI_EXE", "")
            if not exe:
                base = os.environ.get("HOUDINI_PATH", "")
                if base:
                    exe = str(Path(base) / "houdini.exe")
        elif key == "maya":
            exe = os.environ.get("MAYA_EXE", "")
            if not exe:
                base = os.environ.get("MAYA_BIN", "")
                if base:
                    exe = str(Path(base) / "maya.exe")
        elif key == "blender":
            exe = os.environ.get("BLENDER_EXE", "")
        elif key in {"substance", "substance-designer", "substance_designer"}:
            exe = os.environ.get("SUBSTANCE_DESIGNER_EXE", "")

        return exe or "未配置路径"

    def _status_text(self, cfg: DccConfig) -> str:
        if not self._enabled.get(cfg.key, True):
            return "关闭"
        state_dir = cfg.state_dir_func()
        ws_port = state_dir / "ws_port.json"
        if ws_port.exists():
            try:
                text = ws_port.read_text(encoding="utf-8")
                if "port" in text:
                    return "运行中"
            except OSError:
                pass
        return "未启动"

    def _on_toggle(self, key: str) -> None:
        self._enabled[key] = self._checkboxes[key].isChecked()
        self._refresh_status()
        self.toggled.emit(self._enabled.copy())
        self.module_toggled.emit(key, self._enabled[key])

    def _refresh_status(self) -> None:
        for cfg in self._configs:
            label = self._status_labels.get(cfg.key)
            if label:
                label.setText(self._status_text(cfg))
                label.setStyleSheet(
                    "color:#1f7a3d;" if self._enabled.get(cfg.key, True) else "color:#9a6b2f;"
                )

    def enabled_modules(self) -> dict[str, bool]:
        return self._enabled.copy()

    def update_status_map(self, status_map: dict[str, str]) -> None:
        for key, text in status_map.items():
            label = self._status_labels.get(key)
            if not label:
                continue
            label.setText(text)
            if text in {"运行中", "已连接"}:
                label.setStyleSheet("color:#1f7a3d;")
            elif text in {"未响应", "异常"}:
                label.setStyleSheet("color:#b33a3a;")
            elif text in {"关闭"}:
                label.setStyleSheet("color:#9a6b2f;")
            else:
                label.setStyleSheet("color:#4b5563;")

    def _open_exe(self, key: str) -> None:
        path = self._format_path(key)
        if not path or path == "未配置路径":
            return
        try:
            os.startfile(path)
        except OSError:
            pass

    def _open_folder(self, key: str) -> None:
        path = self._format_path(key)
        if not path or path == "未配置路径":
            return
        try:
            os.startfile(str(Path(path).parent))
        except OSError:
            pass
