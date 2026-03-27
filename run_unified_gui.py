"""Launch unified DCC MCP Control Panel GUI."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from houdini_mcp.gui.unified_app import main


if __name__ == "__main__":
    os.environ.setdefault("BLENDER_EXE", "D:/常用软件/Blender 4.2/blender.exe")
    os.environ.setdefault(
        "SUBSTANCE_DESIGNER_EXE",
        r"D:\常用软件\Substance 3D Designer\Adobe Substance 3D Designer.exe",
    )
    os.environ.setdefault("MAYA_BIN", r"C:\Program Files\Autodesk\Maya2026\bin")
    os.environ.setdefault("HOUDINI_PATH", r"C:\Program Files\Side Effects Software\Houdini 20.5.487\bin")
    main()
