# Substance Designer MCP for Codex

## Setup

Edit `C:/Users/wepie/.codex/config.toml`:

```toml
[mcp_servers.substance_designer_mcp]
command = "C:/Program Files/Python311/python.exe"
args = ["-u", "C:/Users/wepie/houdini-mcp/substance_mcp/server_with_gui.py"]

[mcp_servers.substance_designer_mcp.env]
PYTHONUNBUFFERED = "1"
PYTHONPATH = "C:/Users/wepie/houdini-mcp"
SUBSTANCE_DESIGNER_EXE = "D:/常用软件/Substance 3D Designer/Adobe Substance 3D Designer.exe"
```

Then fully restart `Codex`.

## Tools

- `get_scene_state`
- `launch_designer`
- `inspect_sbsar`
- `render_sbsar`
- `cook_sbs`
- `list_outputs`

