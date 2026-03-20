"""Dashboard widget showing server status and statistics."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGroupBox, QFrame, QSizePolicy
)
from PyQt6.QtGui import QFont
from datetime import timedelta


class StatusCard(QFrame):
    """Status card widget."""

    def __init__(self, title: str, value: str = "N/A", parent=None):
        super().__init__(parent)

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #d7dde5;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #5b6773; font-size: 12px;")
        layout.addWidget(self.title_label)

        # Value
        self.value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(20)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet("color: #17202a;")
        self.value_label.setWordWrap(True)
        self.value_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.value_label)

    def set_value(self, value: str):
        """Update value."""
        self.value_label.setText(value)


class DashboardWidget(QWidget):
    """Dashboard tab content."""

    def __init__(self, parent=None, dcc_name: str = "Houdini"):
        super().__init__(parent)
        self.dcc_name = dcc_name

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Title
        title = QLabel("📊 系统状态")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Status cards
        cards_layout = QGridLayout()
        cards_layout.setSpacing(15)

        self.server_status_card = StatusCard("服务器状态", "● 运行中")
        self.server_status_card.value_label.setStyleSheet("color: #2ecc71;")
        cards_layout.addWidget(self.server_status_card, 0, 0)

        self.uptime_card = StatusCard("服务运行时间", "00:00:00")
        cards_layout.addWidget(self.uptime_card, 0, 1)

        self.houdini_status_card = StatusCard("会话节点", "检查中...")
        cards_layout.addWidget(self.houdini_status_card, 0, 2)

        self.backend_pid_card = StatusCard("后台 PID", "—")
        cards_layout.addWidget(self.backend_pid_card, 1, 0)

        self.ws_card = StatusCard("WebSocket", "—")
        cards_layout.addWidget(self.ws_card, 1, 1)

        self.hip_card = StatusCard("场景文件", "—")
        cards_layout.addWidget(self.hip_card, 1, 2)
        cards_layout.setColumnStretch(0, 1)
        cards_layout.setColumnStretch(1, 1)
        cards_layout.setColumnStretch(2, 1)

        layout.addLayout(cards_layout)

        # Connection info group
        connection_group = QGroupBox("🔗 连接状态")
        connection_layout = QVBoxLayout()

        self.claude_status = QLabel("后台服务: 检查中...")
        self.houdini_detail = QLabel(f"{self.dcc_name} 会话: 检查中...")
        self.claude_status.setWordWrap(True)
        self.houdini_detail.setWordWrap(True)

        connection_layout.addWidget(self.claude_status)
        connection_layout.addWidget(self.houdini_detail)

        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)

        # Runtime paths
        path_group = QGroupBox("📁 运行路径")
        path_layout = QVBoxLayout()
        self.state_dir_label = QLabel("状态目录: —")
        self.log_dir_label = QLabel("日志目录: —")
        self.state_dir_label.setWordWrap(True)
        self.log_dir_label.setWordWrap(True)
        path_layout.addWidget(self.state_dir_label)
        path_layout.addWidget(self.log_dir_label)
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        layout.addStretch()

    def update_status(self, status: dict):
        """Update dashboard with server status.

        Args:
            status: Status dict from WebSocket
        """
        # Uptime
        uptime_seconds = status.get("uptime_seconds", 0)
        uptime_str = str(timedelta(seconds=int(uptime_seconds)))
        self.uptime_card.set_value(uptime_str)

        # Houdini status
        houdini_connected = status.get("houdini_connected", False)
        backend_pid = status.get("backend_pid")
        scene_node_count = status.get("scene_node_count")
        hip_file = status.get("hip_file")

        if houdini_connected:
            node_text = str(scene_node_count) if scene_node_count is not None else "就绪"
            self.houdini_status_card.set_value(node_text)
            self.houdini_status_card.value_label.setStyleSheet("color: #2ecc71;")
            if hip_file:
                self.houdini_detail.setText(f"{self.dcc_name} 会话: ✓ 已加载 ({hip_file})")
                self.hip_card.set_value(hip_file)
                self.hip_card.value_label.setToolTip(hip_file)
            else:
                self.houdini_detail.setText(f"{self.dcc_name} 会话: ✓ 已连接")
                self.hip_card.set_value("—")
                self.hip_card.value_label.setToolTip("")
            self.houdini_detail.setStyleSheet("color: #2ecc71;")
        else:
            self.houdini_status_card.set_value("✗ 未找到")
            self.houdini_status_card.value_label.setStyleSheet("color: #e74c3c;")
            self.houdini_detail.setText(f"{self.dcc_name} 会话: ✗ 未运行")
            self.houdini_detail.setStyleSheet("color: #e74c3c;")
            self.hip_card.set_value("—")
            self.hip_card.value_label.setToolTip("")

        # Backend service (assume connected if we're getting status)
        if backend_pid:
            self.claude_status.setText(f"后台服务: ✓ 已连接 (PID {backend_pid})")
            self.backend_pid_card.set_value(str(backend_pid))
        else:
            self.claude_status.setText("后台服务: ✓ 已连接")
            self.backend_pid_card.set_value("—")
        self.claude_status.setStyleSheet("color: #2ecc71;")

    def update_operation(self, op_data: dict):
        """No-op placeholder for removed dashboard operation widgets."""
        return

    def set_connection_info(self, ws_url: str, state_dir: str, log_dir: str):
        self.ws_card.set_value(self._short_path(ws_url))
        self.ws_card.value_label.setToolTip(ws_url)
        self.state_dir_label.setText(f"状态目录: {state_dir}")
        self.log_dir_label.setText(f"日志目录: {log_dir}")

    @staticmethod
    def _short_path(path: str) -> str:
        if len(path) <= 42:
            return path
        return f"...{path[-39:]}"
