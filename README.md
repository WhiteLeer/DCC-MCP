# Houdini MCP

Houdini MCP for `Codex`, built around a persistent local daemon.

## Architecture

This repository now uses a two-layer design:

1. `houdini_mcp.daemon_server`
   A persistent local backend process. It owns the GUI control channel and executes Houdini operations.

2. `houdini_mcp.server_with_gui`
   A lightweight stdio MCP bridge for `Codex`. It forwards tool calls to the daemon.

This avoids the old failure mode where `Codex` starts and stops short-lived MCP subprocesses, causing the GUI WebSocket server to disappear.

## Why this works better

- The GUI talks to a stable daemon instead of a short-lived MCP child process
- `Codex` can restart bridge processes freely without killing the backend
- The backend can be shared by GUI and MCP clients at the same time

## Main entry points

- `python -m houdini_mcp.daemon_server`
  Starts the persistent backend directly
- `启动后台服务.bat`
  Starts the persistent backend directly on Windows
- `python run_gui.py`
  Ensures the daemon is running, then opens the control panel
- `houdini_mcp/server_with_gui.py`
  The MCP bridge that `Codex` should launch
- `python verify_codex_setup.py`
  Verifies Codex config, daemon state, and logs

## Runtime state

The daemon writes runtime state into:

- `C:/Users/wepie/.codex/mcp/houdini-mcp/.running.lock`
- `C:/Users/wepie/.codex/mcp/houdini-mcp/ws_port.json`
- `C:/Users/wepie/.codex/mcp/houdini-mcp/ws_port_<pid>.json`

The GUI and the MCP bridge both use these files to discover the active daemon instance.

## Codex setup

Use the MCP bridge in `C:/Users/wepie/.codex/config.toml`:

```toml
[mcp_servers.houdini_mcp]
command = "python"
args = ["-u", "C:/Users/wepie/houdini-mcp/houdini_mcp/server_with_gui.py"]

[mcp_servers.houdini_mcp.env]
PYTHONUNBUFFERED = "1"
PYTHONPATH = "C:/Users/wepie/houdini-mcp"
```

The daemon is started automatically by the bridge or by `run_gui.py` when needed.

## GUI flow

`MCP控制面板` no longer depends on `Codex` to keep its control channel alive.

It now connects to the persistent daemon. If the daemon is not running, `run_gui.py` will try to launch it first.

## Related docs

- `CODEX_SETUP.md`
- `README_GUI.md`
- `使用说明.md`

## Reference

The direction is aligned with the broader `loonghao` DCC MCP ecosystem, which separates host-facing MCP layers from reusable DCC service components such as `dcc-mcp`, `dcc-mcp-core`, and `dcc-mcp-rpyc`. This is an architectural inference from the repository catalog, not a claim about an exact implementation match. Source: [loonghao repositories](https://github.com/loonghao?language=&q=mcp&sort=stargazers&tab=repositories&type=)
