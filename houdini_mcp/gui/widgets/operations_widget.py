"""Operations history widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QLabel, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
import json


class OperationsWidget(QWidget):
    """Operations history tab."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title and filters
        header_layout = QHBoxLayout()

        title = QLabel("📋 操作历史")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Filter
        header_layout.addWidget(QLabel("过滤:"))

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "成功", "失败", "超时"])
        self.filter_combo.currentTextChanged.connect(self._apply_filter)
        header_layout.addWidget(self.filter_combo)

        # Clear button
        clear_btn = QPushButton("🗑️ 清空历史")
        clear_btn.clicked.connect(self._clear_history)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "时间", "操作", "状态", "耗时", "参数", "详情"
        ])

        # Configure table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #fcfcfd;
                alternate-background-color: #f4f6f8;
                color: #17202a;
                gridline-color: #d7dde5;
                border: 1px solid #cfd6df;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #cfe8ff;
                color: #0f172a;
            }
            QHeaderView::section {
                background-color: #e9eef5;
                color: #17202a;
                padding: 8px;
                border: 1px solid #cfd6df;
                font-weight: bold;
            }
        """)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.itemDoubleClicked.connect(self._show_operation_details)

        # Auto-resize columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table)

    def add_operation(self, op_data: dict):
        """Add operation to history.

        Args:
            op_data: Operation data dict
        """
        timestamp = op_data.get("timestamp", "")
        operation = op_data.get("operation", "unknown")
        status = op_data.get("status", "unknown")
        duration = op_data.get("duration", 0)
        params = op_data.get("params", {})
        error = op_data.get("error")

        # Format time
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
        except:
            time_str = timestamp

        # Insert row at top
        row = 0
        self.table.insertRow(row)

        # Time
        time_item = QTableWidgetItem(time_str)
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 0, time_item)

        # Operation
        op_item = QTableWidgetItem(operation)
        self.table.setItem(row, 1, op_item)

        # Status with color
        if status == "success":
            status_text = "✓ 成功"
            color = QColor(46, 204, 113)  # Green
        elif status == "timeout":
            status_text = "⏰ 超时"
            color = QColor(230, 126, 34)  # Orange
        else:
            status_text = "✗ 失败"
            color = QColor(231, 76, 60)  # Red

        status_item = QTableWidgetItem(status_text)
        status_item.setForeground(color)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, status_item)

        # Duration
        duration_item = QTableWidgetItem(f"{duration:.2f}s")
        duration_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
        self.table.setItem(row, 3, duration_item)

        # Parameters (abbreviated)
        params_str = ", ".join([f"{k}={v}" for k, v in list(params.items())[:3]])
        if len(params) > 3:
            params_str += "..."
        params_item = QTableWidgetItem(params_str)
        self.table.setItem(row, 4, params_item)

        # Details button
        if error:
            short_error = error if len(error) <= 48 else f"{error[:48]}..."
            details_item = QTableWidgetItem(short_error)
            details_item.setForeground(QColor(231, 76, 60))
            details_item.setToolTip(error)
        else:
            details_item = QTableWidgetItem("双击查看")

        self.table.setItem(row, 5, details_item)

        # Store full data in row
        self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, op_data)

        # Limit to 1000 rows
        if self.table.rowCount() > 1000:
            self.table.removeRow(self.table.rowCount() - 1)

    def _apply_filter(self, filter_text: str):
        """Apply filter to table."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 2)  # Status column

            if filter_text == "全部":
                self.table.setRowHidden(row, False)
            elif filter_text == "成功" and "成功" in item.text():
                self.table.setRowHidden(row, False)
            elif filter_text == "失败" and "失败" in item.text():
                self.table.setRowHidden(row, False)
            elif filter_text == "超时" and "超时" in item.text():
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def _clear_history(self):
        """Clear operation history."""
        self.table.setRowCount(0)

    def _show_operation_details(self, item: QTableWidgetItem):
        row = item.row()
        time_item = self.table.item(row, 0)
        if not time_item:
            return

        op_data = time_item.data(Qt.ItemDataRole.UserRole) or {}
        if not op_data:
            return

        details = json.dumps(op_data, indent=2, ensure_ascii=False)
        QMessageBox.information(
            self,
            f"操作详情: {op_data.get('operation', 'unknown')}",
            details,
        )
