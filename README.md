# dcc-mcp

面向 Houdini、Maya、Blender、Substance Designer 的统一 MCP 工具集。

## 设计目标

- 提供统一入口管理多套 DCC 能力
- 采用常驻进程模型，提升长链路稳定性
- 支持 GUI 与 MCP 客户端并行访问

## 架构说明

每个 DCC 后端分为两层：

1. Daemon 服务：维护会话状态与核心能力
2. MCP Bridge：通过标准输入输出转发调用

这种分层可降低进程竞争，提升可维护性。

## 目录结构

- `houdini_mcp/`
- `maya_mcp/`
- `blender_mcp/`
- `substance_mcp/`
- `launcher/`

## 启动方式

```bash
python run_unified_gui.py
```

也可使用仓库内提供的系统脚本。

## 相关文档

- `README_GUI.md`
- `BLENDER_SETUP.md`
- `HOUDINI_SETUP.md`
- `MAYA_SETUP.md`
- `SUBSTANCE_SETUP.md`

