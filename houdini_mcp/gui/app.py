"""GUI Application entry point."""

import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from .main_window import MainWindow


def main():
    """Run the GUI application."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Houdini MCP Control Panel")
    app.setOrganizationName("Houdini MCP")

    # Create async event loop for Qt
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Create main window
    window = MainWindow()
    window.show()

    # Run event loop
    with loop:
        sys.exit(loop.run_forever())


if __name__ == "__main__":
    main()
