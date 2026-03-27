# Houdini MCP GUI

The GUI now connects to the persistent Houdini daemon, not to the short-lived `Codex` MCP subprocess.

## Unified Panel

You can now launch a unified panel for all DCCs (Houdini / Maya / Blender / Substance Designer).
The unified panel does NOT auto-open by default.

```powershell
python run_unified_gui.py
```

or use desktop shortcut `DCC_MCP_Control.lnk`.

## Connection model

```text
GUI -> daemon_server
Codex -> MCP bridge -> daemon_server
daemon_server -> ProcessExecutor -> hython operation processes
```

## Behavior

- `run_gui.py` starts the daemon if needed
- the daemon keeps a stable WebSocket endpoint for the GUI
- `Codex` bridge processes can come and go without breaking the GUI
- the unified panel can toggle modules on/off (start/stop daemon)
- status is refreshed by heartbeat (get_status)

## Discovery files

- `C:/Users/wepie/.codex/mcp/houdini-mcp/ws_port.json`
- `C:/Users/wepie/.codex/mcp/houdini-mcp/ws_port_<pid>.json`

## Logs

- daemon: `C:/Users/wepie/.mcp_logs/houdini-mcp-daemon/`
- bridge: `C:/Users/wepie/.mcp_logs/houdini-mcp-bridge/`
- GUI (if open): `C:/Users/wepie/.mcp_logs/houdini-mcp-gui/`

The unified panel aggregates logs and loads historical entries when opened.

## Auto-open control

Set environment variable:

```
DCC_MCP_AUTO_OPEN_GUI=1
```

Default is off.

## Notes

The old in-process WebSocket model was unstable under `Codex` because the host did not keep the MCP subprocess alive long enough for GUI control. The daemon model fixes that boundary.
