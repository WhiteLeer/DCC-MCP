"""Launch DCC MCP Control Panel GUI."""

import sys
import os
import argparse

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from houdini_mcp.gui.app import main
from houdini_mcp.gui.dcc_config import get_dcc_config

if __name__ == "__main__":
    os.environ.setdefault("BLENDER_EXE", "D:/常用软件/Blender 4.2/blender.exe")
    os.environ.setdefault(
        "SUBSTANCE_DESIGNER_EXE",
        r"D:\常用软件\Substance 3D Designer\Adobe Substance 3D Designer.exe",
    )
    os.environ.setdefault("MAYA_BIN", r"C:\Program Files\Autodesk\Maya2026\bin")
    os.environ.setdefault("HOUDINI_PATH", r"C:\Program Files\Side Effects Software\Houdini 20.5.487\bin")

    parser = argparse.ArgumentParser()
    parser.add_argument("--dcc", default="houdini")
    args = parser.parse_args()

    config = get_dcc_config(args.dcc)
    if config.ensure_daemon:
        config.ensure_daemon()
    main(dcc=args.dcc)
