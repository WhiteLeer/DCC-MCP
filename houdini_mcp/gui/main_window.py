"""Main window for Houdini MCP Control Panel."""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette
import asyncio
import websockets
import json
from datetime import datetime
from typing import Optional
from pathlib import Path
import psutil

from .widgets.dashboard_widget import DashboardWidget
from .widgets.operations_widget import OperationsWidget
from .widgets.logs_widget import LogsWidget
from .widgets.settings_widget import SettingsWidget
from houdini_mcp.utils.state_paths import get_state_dir


class MainWindow(QMainWindow):
    """Main window for MCP Control Panel."""

    # Signals for thread-safe UI updates
    status_updated = pyqtSignal(dict)
    log_received = pyqtSignal(dict)
    operation_logged = pyqtSignal(dict)
    process_count_updated = pyqtSignal(dict)
    error_received = pyqtSignal(dict)

    def __init__(
        self,
        ws_url: Optional[str] = None,
        state_dir_func=None,
        dcc_name: str = "Houdini",
        app_title: Optional[str] = None,
        log_dir_prefix: str = "houdini-mcp",
        supports_restart: bool = True,
        port_range: tuple[int, int] = (9876, 9885),
        strict_state: bool = True,
        ensure_daemon_func=None,
    ):
        super().__init__()

        self.ws_url = ws_url or "ws://127.0.0.1:9876"
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.dcc_name = dcc_name
        self.app_title = app_title or f"{dcc_name} MCP 控制面板"
        self._state_dir_func = state_dir_func or get_state_dir
        self._log_dir_prefix = log_dir_prefix
        self._supports_restart = supports_restart
        self._port_range = port_range
        self._strict_state = strict_state
        self._ensure_daemon_func = ensure_daemon_func

        self._init_ui()
        self._connect_signals()

        # Start WebSocket connection
        QTimer.singleShot(1000, self._connect_websocket)

        # Periodic process count update (every 3 seconds)
        self.process_count_timer = QTimer()
        self.process_count_timer.timeout.connect(self._request_process_count)
        self.process_count_timer.start(3000)

        # Periodic status update (every 1 second) for uptime/node refresh
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._request_status)
        self.status_timer.start(1000)

    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle(self.app_title)
        self.setGeometry(100, 100, 1200, 800)

        # Apply dark theme
        self._apply_dark_theme()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header
        header_layout = self._create_header()
        main_layout.addLayout(header_layout)

        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Create tabs
        self.dashboard = DashboardWidget(dcc_name=self.dcc_name)
        self.operations = OperationsWidget()
        self.logs = LogsWidget(log_dir_prefix=self._log_dir_prefix)
        self.settings = SettingsWidget(state_dir_func=self._state_dir_func, log_dir_prefix=self._log_dir_prefix)

        self.tabs.addTab(self.dashboard, "📊 仪表盘")
        self.tabs.addTab(self.operations, "📋 操作历史")
        self.tabs.addTab(self.logs, "📝 日志")
        self.tabs.addTab(self.settings, "⚙️ 设置")

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("正在连接到 MCP 服务器...")

    def _create_header(self) -> QHBoxLayout:
        """Create header with title and control buttons."""
        layout = QHBoxLayout()

        # Title
        title = QLabel(f"⚙️ {self.app_title}")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        layout.addStretch()

        # Process count indicator
        self.process_count_label = QLabel("后台/执行进程: --")
        self.process_count_label.setStyleSheet("color: #3498db; font-weight: bold;")
        layout.addWidget(self.process_count_label)

        # Connection status indicator
        self.connection_status = QLabel("● 未连接")
        self.connection_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        layout.addWidget(self.connection_status)

        # Control buttons
        self.cleanup_btn = QPushButton("🧹 清理旧进程")
        self.cleanup_btn.clicked.connect(self._on_cleanup_clicked)
        layout.addWidget(self.cleanup_btn)

        self.restart_mcp_btn = QPushButton("🔄 重启 MCP 服务器")
        self.restart_mcp_btn.setEnabled(False)
        self.restart_mcp_btn.clicked.connect(self._on_restart_mcp_clicked)
        layout.addWidget(self.restart_mcp_btn)

        return layout

    def _apply_dark_theme(self):
        """Apply a higher-contrast light theme."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#eef2f7"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#17202a"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#fcfcfd"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f4f6f8"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#fcfcfd"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#17202a"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#17202a"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#17202a"))
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor("#1f6feb"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#cfe8ff"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#0f172a"))

        self.setPalette(palette)

        # Additional stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #eef2f7;
                color: #17202a;
            }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #c9d2dc;
                padding: 6px 12px;
                border-radius: 4px;
                color: #17202a;
                min-width: 100px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #f4f6f8;
            }
            QPushButton:pressed {
                background-color: #e9eef5;
            }
            QPushButton:disabled {
                background-color: #eef2f7;
                color: #7b8794;
            }
            QTabWidget::pane {
                border: 1px solid #c9d2dc;
                background-color: #ffffff;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #e9eef5;
                color: #17202a;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 2px solid #1f6feb;
            }
            QTabBar::tab:hover {
                background-color: #dfe7f1;
            }
            QStatusBar {
                background-color: #ffffff;
                color: #17202a;
                border-top: 1px solid #c9d2dc;
            }
            QLabel, QGroupBox {
                color: #17202a;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit, QListWidget, QTableWidget {
                background-color: #fcfcfd;
                color: #17202a;
                border: 1px solid #cfd6df;
                border-radius: 4px;
                selection-background-color: #cfe8ff;
                selection-color: #0f172a;
            }
        """)

    def _connect_signals(self):
        """Connect internal signals."""
        self.status_updated.connect(self._update_status)
        self.log_received.connect(self._handle_log)
        self.operation_logged.connect(self._handle_operation)
        self.process_count_updated.connect(self._update_process_count)
        self.error_received.connect(self._handle_error)

    def _connect_websocket(self):
        """Connect to WebSocket server."""
        asyncio.create_task(self._ws_connect_async())

    def _candidate_ws_urls(self) -> list[str]:
        urls: list[str] = []
        state_files: list[tuple[int, Path]] = []

        try:
            state_dir = self._state_dir_func()
            for path in state_dir.glob("ws_port*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    pid = int(data.get("pid", 0))
                    timestamp = int(data.get("timestamp", 0))
                    if pid > 0 and psutil.pid_exists(pid):
                        state_files.append((timestamp, path))
                except Exception:
                    continue
        except Exception:
            pass

        for _, path in sorted(state_files, key=lambda item: item[0], reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                host = data.get("host", "127.0.0.1")
                port = int(data.get("port", 9876))
                url = f"ws://{host}:{port}"
                if url not in urls:
                    urls.append(url)
            except Exception:
                continue

        if not self._strict_state:
            for port in range(self._port_range[0], self._port_range[1] + 1):
                url = f"ws://127.0.0.1:{port}"
                if url not in urls:
                    urls.append(url)

        return urls

    async def _ws_connect_async(self):
        """Async WebSocket connection."""
        try:
            if self._ensure_daemon_func:
                try:
                    self._ensure_daemon_func()
                except Exception:
                    pass

            last_error = None
            for url in self._candidate_ws_urls():
                try:
                    self.ws = await websockets.connect(url, open_timeout=2)
                    self.ws_url = url
                    self.connected = True
                    break
                except Exception as e:
                    last_error = e
                    continue

            if not self.connected:
                raise last_error or RuntimeError("Unable to connect")

            # Update UI
            self.connection_status.setText("● 已连接")
            self.connection_status.setStyleSheet("color: #2ecc71; font-weight: bold;")
            self.restart_mcp_btn.setEnabled(True)
            self.status_bar.showMessage(f"已连接到 MCP 服务器 ({self.ws_url})", 3000)
            self.logs.load_recent_logs()
            self.logs.add_log(
                {
                    "level": "INFO",
                    "message": f"已连接到后台服务 {self.ws_url}",
                    "timestamp": datetime.now().isoformat(),
                    "source": "gui",
                }
            )
            self.dashboard.set_connection_info(
                self.ws_url,
                str(self._state_dir_func()),
                str(Path.home() / ".mcp_logs"),
            )

            # Start receiving messages
            asyncio.create_task(self._ws_receive_loop())

            # Request initial status and process count
            await self._send_command("get_status", {})
            await self._send_command("get_process_count", {})

        except Exception as e:
            self.connected = False
            self.connection_status.setText("● 连接失败")
            self.connection_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.status_bar.showMessage(
                "连接失败：等待后台服务启动。GUI 会自动重试。"
            )
            self.logs.add_log(
                {
                    "level": "ERROR",
                    "message": f"连接后台服务失败: {e}",
                    "timestamp": datetime.now().isoformat(),
                    "source": "gui",
                }
            )

            # Retry in 5 seconds
            QTimer.singleShot(5000, self._connect_websocket)

    async def _ws_receive_loop(self):
        """Receive messages from WebSocket."""
        if not self.ws:
            return

        try:
            async for message in self.ws:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "status_update":
                    self.status_updated.emit(data["data"])
                elif msg_type == "process_count":
                    self.process_count_updated.emit(data["data"])
                elif msg_type == "log_message":
                    self.log_received.emit(data["data"])
                elif msg_type == "operation_log":
                    self.operation_logged.emit(data["data"])
                elif msg_type == "error":
                    self.error_received.emit(data["data"])

        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            self.connection_status.setText("● 未连接")
            self.connection_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.restart_mcp_btn.setEnabled(False)
            self.process_count_label.setText("后台/执行进程: --")
            self.status_bar.showMessage("与 MCP 服务器断开连接")
            self.logs.add_log(
                {
                    "level": "ERROR",
                    "message": "与 MCP 服务器断开连接，5 秒后自动重试",
                    "timestamp": datetime.now().isoformat(),
                    "source": "gui",
                }
            )

            # Retry connection
            QTimer.singleShot(5000, self._connect_websocket)

    async def _send_command(self, command: str, params: dict):
        """Send command to MCP server."""
        if not self.ws or not self.connected:
            QMessageBox.warning(self, "未连接", "未连接到 MCP 服务器")
            return

        message = {
            "type": command,
            "data": params
        }

        await self.ws.send(json.dumps(message))

    def _update_status(self, status: dict):
        """Update UI with server status."""
        self.dashboard.update_status(status)

    def _update_process_count(self, count_data: dict):
        """Update process count display."""
        backend_count = count_data.get("backend_count")
        worker_count = count_data.get("worker_count")
        hython_count = count_data.get("hython_count", 0)

        if backend_count is None or worker_count is None:
            backend_count = 1 if hython_count > 0 else 0
            worker_count = max(hython_count - backend_count, 0)

        if backend_count == 0:
            color = "#e74c3c"
        elif worker_count > 0:
            color = "#f39c12"
        else:
            color = "#2ecc71"

        status = f"后台 {backend_count} | 执行 {worker_count}"
        if worker_count > 1:
            status += " ⚠️"

        self.process_count_label.setText(f"后台/执行进程: {status}")
        self.process_count_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _handle_log(self, log_data: dict):
        """Handle incoming log message."""
        self.logs.add_log(log_data)

    def _handle_operation(self, op_data: dict):
        """Handle incoming operation log."""
        self.operations.add_operation(op_data)
        self.dashboard.update_operation(op_data)

    def _handle_error(self, error_data: dict):
        """Handle server-side error messages."""
        error_text = error_data.get("error", "未知错误")
        details = error_data.get("details")
        message = error_text if not details else f"{error_text} | {details}"
        self.logs.add_log(
            {
                "level": "ERROR",
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "source": "daemon",
            }
        )
        self.status_bar.showMessage(f"错误: {error_text}", 8000)

    def _request_process_count(self):
        """Periodically request process count."""
        if self.connected:
            asyncio.create_task(self._send_command("get_process_count", {}))

    def _request_status(self):
        """Periodically request server status."""
        if self.connected:
            asyncio.create_task(self._send_command("get_status", {}))

    def _on_cleanup_clicked(self):
        """Handle cleanup old processes button click."""
        process_hint = {
            "houdini": "hython",
            "maya": "mayapy",
            "blender": "blender",
            "substance": "substance/python",
        }.get(self.dcc_name.lower().split()[0], self.dcc_name)

        reply = QMessageBox.question(
            self,
            "清理旧进程",
            f"强制清理 {self.dcc_name} 相关旧进程？\n\n"
            f"目标: {process_hint}\n"
            "这会清理可能卡住的后台服务或执行进程，当前连接会短暂断开。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            asyncio.create_task(self._cleanup_old_processes())

    async def _cleanup_old_processes(self):
        """Cleanup old DCC-related processes."""
        try:
            import psutil
            import os
            import json

            current_pid = os.getpid()
            killed_count = 0
            target_pids = set()

            # 1) 优先清理当前 DCC 状态目录中的 daemon PID
            try:
                state_dir = self._state_dir_func()
                for path in Path(state_dir).glob("ws_port*.json"):
                    try:
                        data = json.loads(path.read_text(encoding="utf-8"))
                        pid = int(data.get("pid", 0))
                        if pid > 0 and pid != current_pid and psutil.pid_exists(pid):
                            target_pids.add(pid)
                    except Exception:
                        continue
            except Exception:
                pass

            # 2) 根据 DCC 类型清理明显卡住的执行进程
            markers = []
            dcc_lower = self.dcc_name.lower()
            if "houdini" in dcc_lower:
                markers = ["hython", "houdini_mcp"]
            elif "maya" in dcc_lower:
                markers = ["mayapy", "maya_mcp"]
            elif "blender" in dcc_lower:
                markers = ["blender", "blender_mcp"]
            elif "substance" in dcc_lower:
                markers = ["substance_mcp", "substance-designer"]

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.pid == current_pid:
                        continue
                    name = (proc.info.get('name') or '').lower()
                    cmdline = " ".join(proc.info.get('cmdline') or []).lower()
                    if any(m in name or m in cmdline for m in markers):
                        target_pids.add(proc.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            for pid in list(target_pids):
                try:
                    psutil.Process(pid).kill()
                    killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if killed_count > 0:
                self.status_bar.showMessage(f"已清理 {killed_count} 个旧进程", 5000)
                QMessageBox.information(
                    self,
                    "清理完成",
                    f"已终止 {killed_count} 个 {self.dcc_name} 相关进程。\n\n如需重连，稍等几秒后会自动恢复。"
                )
            else:
                self.status_bar.showMessage("没有找到需要清理的旧进程", 3000)
                QMessageBox.information(self, "清理完成", "没有找到需要清理的进程。")

        except Exception as e:
            QMessageBox.critical(self, "清理失败", f"清理进程失败:\n{e}")
            self.status_bar.showMessage(f"清理失败: {e}")

    def _on_restart_mcp_clicked(self):
        """Handle restart MCP server button click."""
        reply = QMessageBox.question(
            self,
            "重启 MCP 服务器",
            f"重启 {self.dcc_name} 后台服务？\n\n后台服务会自重启，这会应用服务端代码修改。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            asyncio.create_task(self._send_command("restart_mcp_server", {}))
            self.status_bar.showMessage("正在重启 MCP 服务器...")

    def closeEvent(self, event):
        """Handle window close."""
        if self.ws and self.connected:
            asyncio.create_task(self.ws.close())

        event.accept()
