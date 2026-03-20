# DCC MCP (Houdini / Maya / Blender / Substance)

Unified DCC MCP toolkit for `Codex`, based on **persistent local daemons**.

Supported DCCs:
- Houdini
- Maya
- Blender
- Substance Designer

## Architecture

Each DCC uses the same two-layer model:

1. `*_mcp.daemon_server`  
Persistent local backend. Owns GUI control channel and DCC session/runtime state.

2. `*_mcp.server_with_gui`  
Lightweight stdio MCP bridge for `Codex`. Forwards tool calls to daemon.

This avoids short-lived MCP subprocess issues and keeps GUI + MCP stable.

### 中文架构图（统一面板 + 四后端）

```mermaid
flowchart TB
    U["用户"] --> GUI["统一面板 / 单独面板"]
    C["Codex / MCP 客户端"] --> B1["Houdini Bridge"]
    C --> B2["Maya Bridge"]
    C --> B3["Blender Bridge"]
    C --> B4["Substance Bridge"]

    GUI --> B1
    GUI --> B2
    GUI --> B3
    GUI --> B4

    B1 --> D1["Houdini Daemon"]
    B2 --> D2["Maya Daemon"]
    B3 --> D3["Blender Daemon"]
    B4 --> D4["Substance Daemon"]

    D1 --> E1["Houdini 会话/进程"]
    D2 --> E2["Maya 会话/进程"]
    D3 --> E3["Blender 后台进程"]
    D4 --> E4["Substance 会话/进程"]

    D1 -.发现状态.-> S1["~/.codex/mcp/houdini-mcp/ws_port*.json"]
    D2 -.发现状态.-> S2["~/.codex/mcp/maya-mcp/ws_port*.json"]
    D3 -.发现状态.-> S3["~/.codex/mcp/blender-mcp/ws_port*.json"]
    D4 -.发现状态.-> S4["~/.codex/mcp/substance-designer-mcp/ws_port*.json"]

    classDef gui fill:#eaf4ff,stroke:#2f6fed,color:#0f2a56;
    classDef bridge fill:#fff5e8,stroke:#d98a2b,color:#5a3300;
    classDef daemon fill:#eafbef,stroke:#24a148,color:#103b1f;
    classDef runtime fill:#f5f0ff,stroke:#7a52c7,color:#2f1b5a;
    classDef state fill:#f7f7f8,stroke:#8a8f98,color:#2c2f33;

    class GUI gui;
    class B1,B2,B3,B4 bridge;
    class D1,D2,D3,D4 daemon;
    class E1,E2,E3,E4 runtime;
    class S1,S2,S3,S4 state;
```

### 中文链路图（以 Blender 为例）

```mermaid
flowchart LR
    A["用户点击一键流程"] --> B["import_geometry"]
    B --> C["clean_scene / merge_by_distance"]
    C --> D["recalculate_normals / shade_smooth"]
    D --> E["decimate_mesh"]
    E --> F["triangulate_mesh（可选）"]
    F --> G["export_fbx"]
    G --> H["输出: 最终 FBX"]

    classDef op fill:#eaf4ff,stroke:#2f6fed,color:#0f2a56;
    class A,B,C,D,E,F,G,H op;
```

## What You Get

- Stable daemon-driven control plane
- GUI + Codex can work at the same time
- Auto daemon bootstrap when launching GUI/bridge
- Unified control panel for all 4 DCCs

## Main Entry Points

### Unified panel
- `python run_unified_gui.py`
- `启动统一MCP面板.bat`
- Desktop shortcut: `DCC_MCP_Control.lnk`

### Per-DCC GUI
- Houdini: `python run_gui.py`
- Maya: `python run_maya_gui.py`
- Blender: `python run_blender_gui.py`
- Substance: `python run_substance_gui.py`

### MCP bridge (for Codex)
- Houdini: `houdini_mcp/server_with_gui.py`
- Maya: `maya_mcp/server_with_gui.py`
- Blender: `blender_mcp/server_with_gui.py`
- Substance: `substance_mcp/server_with_gui.py`

### Verification
- `python verify_codex_setup.py`

## Runtime State

Daemon state files are written under:

- Houdini: `~/.codex/mcp/houdini-mcp/`
- Maya: `~/.codex/mcp/maya-mcp/`
- Blender: `~/.codex/mcp/blender-mcp/`
- Substance: `~/.codex/mcp/substance-designer-mcp/`

Each contains:
- `.running.lock`
- `ws_port.json`
- `ws_port_<pid>.json`

## Codex Config Example

```toml
[mcp_servers.houdini_mcp]
command = "python"
args = ["-u", "C:/Users/wepie/dcc-mcp/houdini_mcp/server_with_gui.py"]

[mcp_servers.maya_mcp]
command = "python"
args = ["-u", "C:/Users/wepie/dcc-mcp/maya_mcp/server_with_gui.py"]

[mcp_servers.blender_mcp]
command = "python"
args = ["-u", "C:/Users/wepie/dcc-mcp/blender_mcp/server_with_gui.py"]

[mcp_servers.substance_designer_mcp]
command = "python"
args = ["-u", "C:/Users/wepie/dcc-mcp/substance_mcp/server_with_gui.py"]
```

## Blender Notes

Default Blender path used by launcher:
- `D:/常用软件/Blender 4.2/blender.exe`

More details:
- `BLENDER_SETUP.md`

## Related Docs

- `CODEX_SETUP.md`
- `README_GUI.md`
- `MAYA_SETUP.md`
- `SUBSTANCE_SETUP.md`
- `BLENDER_SETUP.md`
- `使用说明.md`
