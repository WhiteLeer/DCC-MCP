"""Launch Houdini MCP Control Panel GUI."""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from houdini_mcp.daemon_launcher import ensure_daemon_running
from houdini_mcp.gui.app import main

if __name__ == "__main__":
    ensure_daemon_running()
    main()
