"""Settings widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLineEdit, QSpinBox, QComboBox,
    QPushButton, QFileDialog, QLabel, QMessageBox
)
from PyQt6.QtGui import QFont
import os
import json

from houdini_mcp.utils.state_paths import get_ws_port_file, get_state_dir


class SettingsWidget(QWidget):
    """Settings tab."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Title
        title = QLabel("⚙️ 配置设置")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Runtime info group
        runtime_group = QGroupBox("运行信息")
        runtime_layout = QFormLayout()

        self.state_dir_input = QLineEdit()
        self.state_dir_input.setReadOnly(True)
        self.state_dir_input.setText(str(get_state_dir()))
        runtime_layout.addRow("状态目录:", self.state_dir_input)

        self.log_dir_input = QLineEdit()
        self.log_dir_input.setReadOnly(True)
        self.log_dir_input.setText(os.path.expanduser("~/.mcp_logs"))
        runtime_layout.addRow("日志目录:", self.log_dir_input)

        runtime_group.setLayout(runtime_layout)
        layout.addWidget(runtime_group)

        # Logging group
        logging_group = QGroupBox("日志设置")
        logging_layout = QFormLayout()

        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setCurrentText("INFO")
        logging_layout.addRow("日志级别:", self.log_level)

        log_hint = QLabel("日志分目录写入 daemon / bridge / gui。当前 GUI 仅显示最新 200 行。")
        log_hint.setWordWrap(True)
        logging_layout.addRow("", log_hint)

        logging_group.setLayout(logging_layout)
        layout.addWidget(logging_group)

        # WebSocket group
        ws_group = QGroupBox("WebSocket 服务器")
        ws_layout = QFormLayout()

        self.ws_port = QSpinBox()
        self.ws_port.setRange(1024, 65535)
        self.ws_port.setValue(9876)
        ws_layout.addRow("端口:", self.ws_port)

        # Try to load actual port from state file
        try:
            ws_port_file = get_ws_port_file()
            if ws_port_file.exists():
                data = json.loads(ws_port_file.read_text(encoding="utf-8"))
                port = int(data.get("port", 9876))
                self.ws_port.setValue(port)
        except Exception:
            pass

        ws_group.setLayout(ws_layout)
        layout.addWidget(ws_group)

        layout.addStretch()

        # Action buttons (reserve space for future)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        layout.addLayout(button_layout)
