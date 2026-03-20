"""Launch Blender MCP Control Panel GUI."""

import os
import sys
import threading

sys.path.insert(0, os.path.dirname(__file__))

from blender_mcp.daemon_launcher import ensure_daemon_running
from houdini_mcp.gui.app import main


if __name__ == "__main__":
    os.environ.setdefault("BLENDER_EXE", "D:/常用软件/Blender 4.2/blender.exe")
    threading.Thread(target=ensure_daemon_running, daemon=True).start()
    main(dcc="blender")
