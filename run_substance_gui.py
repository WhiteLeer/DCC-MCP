"""Launch Substance Designer MCP Control Panel GUI."""

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(__file__))

from substance_mcp.daemon_launcher import ensure_daemon_running
from houdini_mcp.gui.app import main


if __name__ == "__main__":
    os.environ.setdefault(
        "SUBSTANCE_DESIGNER_EXE",
        r"D:\常用软件\Substance 3D Designer\Adobe Substance 3D Designer.exe",
    )
    threading.Thread(target=ensure_daemon_running, daemon=True).start()
    main(dcc="substance-designer")

