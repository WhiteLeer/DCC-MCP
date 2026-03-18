"""Launch DCC MCP Control Panel GUI."""

import sys
import os
import argparse

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from houdini_mcp.gui.app import main
from houdini_mcp.gui.dcc_config import get_dcc_config

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dcc", default="houdini")
    args = parser.parse_args()

    config = get_dcc_config(args.dcc)
    if config.ensure_daemon:
        config.ensure_daemon()
    main(dcc=args.dcc)
