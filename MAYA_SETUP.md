# Maya MCP for Codex

## Setup

Edit `C:/Users/wepie/.codex/config.toml`:

```toml
[mcp_servers.maya_mcp]
command = "C:/Program Files/Autodesk/Maya2026/bin/mayapy.exe"
args = ["-u", "C:/Users/wepie/dcc-mcp/maya_mcp/server_with_gui.py"]

[mcp_servers.maya_mcp.env]
PYTHONUNBUFFERED = "1"
PYTHONPATH = "C:/Users/wepie/dcc-mcp"
MAYA_BIN = "C:/Program Files/Autodesk/Maya2026/bin"
```

Then fully restart `Codex`.

## What starts when

- `Codex` starts the MCP bridge in `maya_mcp/server_with_gui.py`
- The bridge ensures the persistent Maya daemon is running
- The daemon exposes the stable local WebSocket endpoint used by the GUI (if needed)

## Runtime state

The daemon publishes discovery files here:

- `C:/Users/wepie/.codex/mcp/maya-mcp/.running.lock`
- `C:/Users/wepie/.codex/mcp/maya-mcp/ws_port.json`
- `C:/Users/wepie/.codex/mcp/maya-mcp/ws_port_<pid>.json`

## Tools

- `get_scene_state`
- `create_poly_cube`
- `freeze_transform`
- `delete_history`
- `center_pivot`
- `create_locator`

