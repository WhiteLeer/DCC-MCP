"""Logs widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QComboBox, QLabel, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor, QColor
from datetime import datetime
from pathlib import Path
import os


class LogsWidget(QWidget):
    """Logs tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[dict] = []

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("📝 服务器日志")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Level filter
        header_layout.addWidget(QLabel("级别:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["全部", "DEBUG", "INFO", "WARNING", "ERROR"])
        header_layout.addWidget(self.level_combo)

        # Search
        header_layout.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索日志...")
        self.search_input.setMaximumWidth(200)
        header_layout.addWidget(self.search_input)

        # Clear button
        clear_btn = QPushButton("🗑️ 清空日志")
        clear_btn.clicked.connect(self._clear_logs)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #fcfcfd;
                color: #17202a;
                border: 1px solid #cfd6df;
                border-radius: 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                selection-background-color: #cfe8ff;
                selection-color: #0f172a;
            }
        """)

        # Use monospace font
        font = QFont("Consolas", 10)
        self.log_text.setFont(font)

        layout.addWidget(self.log_text)

        # Auto-scroll checkbox
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.auto_scroll = True
        auto_scroll_btn = QPushButton("⬇ 自动滚动: 开")
        auto_scroll_btn.setCheckable(True)
        auto_scroll_btn.setChecked(True)
        auto_scroll_btn.clicked.connect(self._toggle_auto_scroll)
        footer_layout.addWidget(auto_scroll_btn)

        self.auto_scroll_btn = auto_scroll_btn

        layout.addLayout(footer_layout)

        self.level_combo.currentTextChanged.connect(self._render_logs)
        self.search_input.textChanged.connect(self._render_logs)

    def add_log(self, log_data: dict):
        """Add log message.

        Args:
            log_data: Log data dict with level, message, timestamp
        """
        entry = {
            "level": str(log_data.get("level", "INFO")).upper(),
            "message": str(log_data.get("message", "")),
            "timestamp": str(log_data.get("timestamp", "")),
            "source": str(log_data.get("source", "")),
        }
        self._entries.append(entry)
        self._entries = self._entries[-5000:]
        self._render_logs()

    def _clear_logs(self):
        """Clear all logs."""
        self.log_text.clear()
        self._entries.clear()

    def _toggle_auto_scroll(self, checked: bool):
        """Toggle auto-scroll."""
        self.auto_scroll = checked
        self.auto_scroll_btn.setText(
            "⬇ 自动滚动: 开" if checked else "⬇ 自动滚动: 关"
        )

    def load_recent_logs(self):
        """Load recent daemon/bridge/gui logs from disk."""
        self._entries.clear()
        log_root = Path.home() / ".mcp_logs"
        targets = [
            ("daemon", log_root / "houdini-mcp-daemon" / "houdini-mcp-daemon_latest.log"),
            ("bridge", log_root / "houdini-mcp-bridge" / "houdini-mcp-bridge_latest.log"),
            ("gui", log_root / "houdini-mcp-gui" / "houdini-mcp-gui_latest.log"),
        ]

        for source, path in targets:
            if not path.exists():
                continue

            try:
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-200:]
            except OSError:
                continue

            for line in lines:
                self._entries.append(self._parse_log_line(line, source))

        self._entries = self._entries[-5000:]
        self._render_logs()

    def _parse_log_line(self, line: str, source: str) -> dict:
        parts = [part.strip() for part in line.split("|", 4)]
        if len(parts) >= 5:
            timestamp, _, level, _, message = parts
            return {
                "timestamp": timestamp,
                "level": level.upper(),
                "message": message,
                "source": source,
            }

        return {
            "timestamp": "",
            "level": "INFO",
            "message": line,
            "source": source,
        }

    def _render_logs(self):
        level_filter = self.level_combo.currentText()
        search_text = self.search_input.text().strip().lower()

        self.log_text.clear()
        for entry in self._entries:
            if level_filter != "全部" and entry["level"] != level_filter:
                continue

            haystack = f"{entry['message']} {entry.get('source', '')}".lower()
            if search_text and search_text not in haystack:
                continue

            self.log_text.setTextColor(QColor(self._level_color(entry["level"])))
            self.log_text.append(self._format_log_line(entry))

        if self.auto_scroll:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)

    def _format_log_line(self, entry: dict) -> str:
        timestamp = entry.get("timestamp", "")
        source = entry.get("source", "")

        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
        except Exception:
            time_str = timestamp[:19] if timestamp else "--:--:--"

        source_label = f"[{source}]" if source else ""
        return f"[{time_str}] [{entry['level']:<7}] {source_label} {entry['message']}".strip()

    def _level_color(self, level: str) -> str:
        if level == "ERROR":
            return "#c0392b"
        if level == "WARNING":
            return "#b9770e"
        if level == "DEBUG":
            return "#566573"
        return "#17202a"
