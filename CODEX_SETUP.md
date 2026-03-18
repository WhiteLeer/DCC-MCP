# Houdini MCP for Codex

## Setup

Edit `C:/Users/wepie/.codex/config.toml`:

```toml
[mcp_servers.houdini_mcp]
command = "python"
args = ["-u", "C:/Users/wepie/houdini-mcp/houdini_mcp/server_with_gui.py"]

[mcp_servers.houdini_mcp.env]
PYTHONUNBUFFERED = "1"
PYTHONPATH = "C:/Users/wepie/houdini-mcp"
```

Then fully restart `Codex`.

## What starts when

- `Codex` starts the MCP bridge in `houdini_mcp/server_with_gui.py`
- The bridge itself should run under normal `python`, not `hython`
- The bridge ensures the persistent daemon is running
- The daemon exposes the stable local WebSocket endpoint used by the GUI

## GUI behavior

`run_gui.py` also ensures the daemon is running before opening the control panel.

That means:

- opening the GUI does not require `Codex` to keep a child process alive
- closing `Codex` no longer needs to kill the control backend immediately

## Runtime state

The daemon publishes discovery files here:

- `C:/Users/wepie/.codex/mcp/houdini-mcp/.running.lock`
- `C:/Users/wepie/.codex/mcp/houdini-mcp/ws_port.json`
- `C:/Users/wepie/.codex/mcp/houdini-mcp/ws_port_<pid>.json`

## Troubleshooting

If the GUI cannot connect:

1. Check that `Codex` config contains `houdini_mcp`
2. Check that `C:/Users/wepie/.codex/mcp/houdini-mcp/ws_port.json` exists
3. Check `C:/Users/wepie/.mcp_logs/houdini-mcp-daemon/`
4. Check `C:/Users/wepie/.mcp_logs/houdini-mcp-bridge/`

You can also run:

```text
python verify_codex_setup.py
```

## Source

OpenAI documents the shared `Codex` MCP config location in `~/.codex/config.toml`: [Docs MCP](https://developers.openai.com/learn/docs-mcp)
