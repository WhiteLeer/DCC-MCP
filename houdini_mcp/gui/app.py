"""GUI Application entry point."""

import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from .main_window import MainWindow
from .dcc_config import get_dcc_config


def main(dcc: str = "houdini"):
    """Run the GUI application."""
    config = get_dcc_config(dcc)
    # Create Qt application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName(f"{config.display_name} MCP Control Panel")
    app.setOrganizationName(f"{config.display_name} MCP")

    # Create async event loop for Qt
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Create main window
    window = MainWindow(
        dcc_name=config.display_name,
        state_dir_func=config.state_dir_func,
        log_dir_prefix=config.log_dir_prefix,
        app_title=f"{config.display_name} MCP 控制面板",
        supports_restart=config.supports_restart,
        port_range=config.port_range,
        strict_state=config.strict_state,
        ensure_daemon_func=config.ensure_daemon,
    )
    window.show()

    # Run event loop
    with loop:
        sys.exit(loop.run_forever())


if __name__ == "__main__":
    main()
