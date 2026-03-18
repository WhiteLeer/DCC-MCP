"""Launch Maya MCP Control Panel GUI."""

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(__file__))

from maya_mcp.daemon_launcher import ensure_daemon_running
from houdini_mcp.gui.app import main


if __name__ == "__main__":
    os.environ.setdefault("MAYA_BIN", r"C:\Program Files\Autodesk\Maya2026\bin")
    threading.Thread(target=ensure_daemon_running, daemon=True).start()
    main(dcc="maya")
