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

    def __init__(
        self,
        parent=None,
        log_dir_prefix: str = "houdini-mcp",
        log_dir_prefixes: list[str] | None = None,
        compact: bool = False,
    ):
        super().__init__(parent)
        self._log_dir_prefix = log_dir_prefix
        self._log_dir_prefixes = log_dir_prefixes
        self._compact = compact
        self._entries: list[dict] = []
        self._flow_only = compact

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        if self._compact:
            layout.setContentsMargins(6, 6, 6, 6)
            layout.setSpacing(6)
        else:
            layout.setContentsMargins(15, 15, 15, 15)
            layout.setSpacing(10)

        if not self._compact:
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
        else:
            self.level_combo = None
            self.search_input = None

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        if self._compact:
            self.log_text.setStyleSheet("""
                QTextEdit {
                    background-color: #ffffff;
                    color: #1f2933;
                    border: 1px solid #d6dde6;
                    border-radius: 8px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 12px;
                    selection-background-color: #d7e3ff;
                    selection-color: #1f2933;
                }
            """)
        else:
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
        self.auto_scroll = True
        if not self._compact:
            footer_layout = QHBoxLayout()
            footer_layout.addStretch()

            auto_scroll_btn = QPushButton("⬇ 自动滚动: 开")
            auto_scroll_btn.setCheckable(True)
            auto_scroll_btn.setChecked(True)
            auto_scroll_btn.clicked.connect(self._toggle_auto_scroll)
            footer_layout.addWidget(auto_scroll_btn)

            self.auto_scroll_btn = auto_scroll_btn
            layout.addLayout(footer_layout)
        else:
            self.auto_scroll_btn = None

        if self.level_combo is not None:
            self.level_combo.currentTextChanged.connect(self._render_logs)
        if self.search_input is not None:
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

    def set_log_prefixes(self, prefixes: list[str]) -> None:
        self._log_dir_prefixes = prefixes

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
        prefixes = self._log_dir_prefixes or [self._log_dir_prefix]

        for prefix in prefixes:
            for kind in ("daemon", "bridge", "gui"):
                logger_name = f"{prefix}-{kind}"
                log_dir = log_root / logger_name
                path = self._pick_log_file(log_dir, logger_name)
                if not path:
                    continue

                try:
                    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-400:]
                except OSError:
                    continue

                source = f"{prefix}:{kind}"
                for line in lines:
                    self._entries.append(self._parse_log_line(line, source))

        self._entries.sort(key=self._entry_sort_key)
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

    def _pick_log_file(self, log_dir: Path, logger_name: str) -> Path | None:
        if not log_dir.exists():
            return None
        latest = log_dir / f"{logger_name}_latest.log"
        if latest.exists():
            try:
                if latest.stat().st_size > 0:
                    return latest
            except OSError:
                pass
        candidates = sorted(
            log_dir.glob(f"{logger_name}_*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for candidate in candidates:
            if candidate.name.endswith("_latest.log"):
                continue
            return candidate
        return latest if latest.exists() else None

    def _entry_sort_key(self, entry: dict) -> float:
        timestamp = entry.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            return 0.0

    def _render_logs(self):
        level_filter = self.level_combo.currentText() if self.level_combo else "全部"
        search_text = self.search_input.text().strip().lower() if self.search_input else ""

        self.log_text.clear()
        shown = 0
        for entry in self._entries:
            if self._should_skip_entry(entry):
                continue
            if level_filter != "全部" and entry["level"] != level_filter:
                continue

            haystack = f"{entry['message']} {entry.get('source', '')}".lower()
            if search_text and search_text not in haystack:
                continue

            self.log_text.setTextColor(QColor(self._entry_color(entry)))
            self.log_text.append(self._format_log_line(entry))
            shown += 1

        if shown == 0 and self._flow_only:
            self.log_text.setTextColor(QColor("#6b7280"))
            self.log_text.append("暂无流程日志。执行一次工具调用后会显示完整调用链。")

        if self.auto_scroll:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)

    def _should_skip_entry(self, entry: dict) -> bool:
        msg = str(entry.get("message", ""))
        level = str(entry.get("level", "INFO")).upper()

        if self._is_noise_message(msg):
            return True

        if self._flow_only:
            if "FLOW |" in msg:
                return False
            if level in {"ERROR", "WARNING"}:
                return False
            return True

        return False

    def _is_noise_message(self, message: str) -> bool:
        text = message.lower()
        noise_tokens = [
            "client connected",
            "client disconnected",
            "starting houdini mcp bridge",
            "starting maya mcp bridge",
            "starting blender mcp bridge",
            "starting substance designer mcp bridge",
            "file logging enabled",
            "daemon listening on",
            "failed to cleanup old logs",
            "found stale lock file",
        ]
        return any(token in text for token in noise_tokens)

    def _format_log_line(self, entry: dict) -> str:
        timestamp = entry.get("timestamp", "")
        source = entry.get("source", "")
        message = str(entry.get("message", ""))

        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
        except Exception:
            time_str = timestamp[:19] if timestamp else "--:--:--"

        if "FLOW |" in message:
            pretty = self._pretty_flow_message(message, source)
            return f"[{time_str}] {pretty}"

        source_label = f"[{source}]" if source else ""
        return f"[{time_str}] [{entry['level']:<7}] {source_label} {message}".strip()

    def _pretty_flow_message(self, message: str, source: str) -> str:
        parts = [p.strip() for p in message.split("|")]
        if len(parts) < 4:
            return message
        dcc_label = self._source_to_dcc(source)
        op = parts[1]
        status = "OK" if parts[2].lower() == "success" else "FAIL"
        duration = parts[3]
        extras = [p for p in parts[4:] if p]
        lines = [f"[{dcc_label}] {op} [{status}] {duration}"]
        for extra in extras:
            if extra.startswith("in="):
                lines.append(f"  in: {extra[3:]}")
            elif extra.startswith("out="):
                lines.append(f"  out: {extra[4:]}")
            elif extra.startswith("error="):
                lines.append(f"  error: {extra[6:]}")
            else:
                lines.append(f"  {extra}")
        return "\n".join(lines)

    def _source_to_dcc(self, source: str) -> str:
        text = (source or "").lower()
        if "houdini" in text:
            return "Houdini"
        if "blender" in text:
            return "Blender"
        if "maya" in text:
            return "Maya"
        if "substance" in text:
            return "Substance"
        return "DCC"

    def _entry_color(self, entry: dict) -> str:
        message = str(entry.get("message", ""))
        if "FLOW |" in message:
            dcc = self._source_to_dcc(str(entry.get("source", "")))
            return self._dcc_color(dcc)
        return self._level_color(str(entry.get("level", "INFO")).upper())

    def _dcc_color(self, dcc: str) -> str:
        if dcc == "Houdini":
            return "#8b5cf6"
        if dcc == "Blender":
            return "#2563eb"
        if dcc == "Maya":
            return "#0f766e"
        if dcc == "Substance":
            return "#b45309"
        return "#1f2933"

    def _level_color(self, level: str) -> str:
        if level == "ERROR":
            return "#c0392b"
        if level == "WARNING":
            return "#b9770e"
        if level == "DEBUG":
            return "#566573"
        return "#1f2933"
