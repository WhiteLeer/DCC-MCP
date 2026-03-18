# Houdini MCP GUI

The GUI now connects to the persistent Houdini daemon, not to the short-lived `Codex` MCP subprocess.

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

## Discovery files

- `C:/Users/wepie/.codex/mcp/houdini-mcp/ws_port.json`
- `C:/Users/wepie/.codex/mcp/houdini-mcp/ws_port_<pid>.json`

## Logs

- daemon: `C:/Users/wepie/.mcp_logs/houdini-mcp-daemon/`
- bridge: `C:/Users/wepie/.mcp_logs/houdini-mcp-bridge/`

## Notes

The old in-process WebSocket model was unstable under `Codex` because the host did not keep the MCP subprocess alive long enough for GUI control. The daemon model fixes that boundary.
