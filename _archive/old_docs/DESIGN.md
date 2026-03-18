# Houdini MCP Professional GUI - Design Document

## 🎯 目标

创建专业级的MCP控制面板，支持**不重启Claude Code即可重启MCP服务器**。

---

## 🏗️ 架构设计

### 三层架构

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Code                          │
│               (无需重启，无感知)                         │
└───────────────────────┬─────────────────────────────────┘
                        │ spawn + JSON-RPC (stdin/stdout)
                        ▼
┌─────────────────────────────────────────────────────────┐
│              MCP Server Core                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │ FastMCP Engine                                  │   │
│  │  - 处理JSON-RPC协议                             │   │
│  │  - 工具注册与调用                               │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ WebSocket Control Server (port 9876)            │   │
│  │  - 接收GUI控制命令                              │   │
│  │  - 推送状态更新 (日志、性能)                    │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Houdini Connection Manager (可热重启)           │   │
│  │  - 连接池管理                                   │   │
│  │  - 超时保护                                     │   │
│  │  - 自动重连                                     │   │
│  └─────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────┘
                        │ WebSocket (ws://localhost:9876)
                        ▼
┌─────────────────────────────────────────────────────────┐
│              GUI Control Panel (独立进程)               │
│  ┌─────────────────────────────────────────────────┐   │
│  │ PyQt6 Main Window                               │   │
│  │  - Dashboard (状态监控)                         │   │
│  │  - Operations (操作历史)                        │   │
│  │  - Houdini Scene Preview (场景预览)             │   │
│  │  - Performance Monitor (性能图表)               │   │
│  │  - Settings (配置管理)                          │   │
│  │  - Logs (实时日志)                              │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 核心功能

### 1. 热重启机制

**不重启进程的情况下重启服务**：

```python
# MCP Server内部
class HoudiniConnectionManager:
    def restart(self):
        """热重启Houdini连接，MCP进程不退出"""
        self.disconnect_all()      # 断开现有连接
        self.clear_cache()         # 清空缓存
        self.reload_config()       # 重新加载配置
        self.reconnect()           # 重新连接
        # MCP Server stdin/stdout通信不受影响 ✅

# GUI触发
gui.restart_button.clicked.connect(lambda: ws.send({
    "command": "restart_houdini"
}))
```

**对Claude Code透明**：
- Claude Code只看到MCP进程一直在运行
- stdin/stdout JSON-RPC通道从未中断
- 工具调用正常，内部已经是新连接

---

## 🎨 GUI界面设计

### 主窗口布局

```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ Houdini MCP Control Panel            [─] [□] [×]         │
├──────────────┬──────────────────────────────────────────────┤
│              │  📊 Dashboard                                │
│  Dashboard   │  ┌─────────────────────────────────────┐    │
│  Operations  │  │ Server Status: ● Running            │    │
│  Scene       │  │ Uptime: 02:34:15                    │    │
│  Performance │  │                                      │    │
│  Settings    │  │ 🔗 Connections:                     │    │
│  Logs        │  │   Claude Code: ✓ Connected          │    │
│              │  │   Houdini 20.5: ✓ PID 26760         │    │
│              │  │                                      │    │
│  [Restart]   │  │ 📈 Statistics (Last Hour):          │    │
│  [Stop]      │  │   Total Operations: 127             │    │
│              │  │   Success Rate: 97.6%               │    │
│              │  │   Avg Response: 0.87s               │    │
│              │  └─────────────────────────────────────┘    │
│              │                                              │
│              │  Recent Operations:                          │
│              │  ┌─────────────────────────────────────┐    │
│              │  │ ✓ create_box        0.23s  [Detail] │    │
│              │  │ ✓ polyreduce        1.45s  [Detail] │    │
│              │  │ ✗ mirror (timeout)  30.0s  [Retry]  │    │
│              │  │ ✓ boolean           2.31s  [Detail] │    │
│              │  └─────────────────────────────────────┘    │
└──────────────┴──────────────────────────────────────────────┘
```

### Operations Tab (操作历史)

```
┌──────────────────────────────────────────────────────────────┐
│  🔍 Filter: [All ▼] [Success ☑] [Failed ☑] [Timeout ☑]       │
├──────────────────────────────────────────────────────────────┤
│  Time      │ Operation    │ Status  │ Duration │ Details     │
├────────────┼──────────────┼─────────┼──────────┼─────────────┤
│ 12:30:45   │ create_box   │ ✓       │ 0.23s    │ [View Log]  │
│ 12:31:02   │ polyreduce   │ ✓       │ 1.45s    │ [View Log]  │
│ 12:31:50   │ mirror       │ ✗ Time  │ 30.00s   │ [Retry]     │
│ 12:32:15   │ boolean      │ ✓       │ 2.31s    │ [View Log]  │
└──────────────────────────────────────────────────────────────┘

Operation Details (选中后显示):
┌──────────────────────────────────────────────────────────────┐
│ Operation: mirror                                            │
│ Status: Failed (Timeout)                                     │
│ Timestamp: 2026-03-16 12:31:50                              │
│                                                              │
│ Parameters:                                                  │
│   geo_path: /obj/geo1                                       │
│   axis: x                                                   │
│   merge: true                                               │
│                                                              │
│ Error: Operation timed out after 30.0s                      │
│                                                              │
│ [Copy Parameters] [Retry with Params] [Export Report]       │
└──────────────────────────────────────────────────────────────┘
```

### Scene Tab (Houdini场景预览)

```
┌──────────────────────────────────────────────────────────────┐
│  📁 Current Scene: untitled.hip                [Refresh]     │
├──────────────────────────────────────────────────────────────┤
│  Node Tree:                    │  Preview:                   │
│  ┌──────────────────────┐      │  ┌──────────────────────┐  │
│  │ /obj                 │      │  │                      │  │
│  │  ├─ geo1             │      │  │    [3D Preview]      │  │
│  │  │  ├─ box1          │      │  │    (需要Houdini     │  │
│  │  │  ├─ polyreduce1   │      │  │     Engine API)      │  │
│  │  │  └─ mirror1       │      │  │                      │  │
│  │  └─ cam1             │      │  └──────────────────────┘  │
│  └──────────────────────┘      │                            │
│                                 │  Node Info:                │
│  [Create Box]                   │  Selected: /obj/geo1/box1 │
│  [Import Geometry]              │  Type: Box                │
│  [Boolean]                      │  Polygons: 24             │
│                                 │  Points: 8                │
└──────────────────────────────────────────────────────────────┘
```

### Performance Tab (性能监控)

```
┌──────────────────────────────────────────────────────────────┐
│  Time Range: [Last Hour ▼]                    [Export CSV]   │
├──────────────────────────────────────────────────────────────┤
│  Response Time Trend:                                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │ 3.0s ┤                                              │     │
│  │      │            ╭─╮                               │     │
│  │ 2.0s ┤       ╭────╯ ╰─╮                            │     │
│  │      │   ╭───╯         ╰──╮                        │     │
│  │ 1.0s ┤───╯                ╰───────────────         │     │
│  │      │                                              │     │
│  │ 0.0s └────┬────┬────┬────┬────┬────┬────┬────┬     │     │
│  │         11:30  11:45  12:00  12:15  12:30         │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  Operation Distribution:        Success Rate:                │
│  ┌─────────────────────┐        ┌─────────────────────┐     │
│  │                     │        │                     │     │
│  │  create_box:  35%   │        │   ████████████░░ 95%│     │
│  │  polyreduce:  25%   │        │                     │     │
│  │  mirror:      20%   │        └─────────────────────┘     │
│  │  boolean:     15%   │                                     │
│  │  import:       5%   │        Avg: 0.87s                   │
│  │                     │        P95: 2.34s                   │
│  └─────────────────────┘        P99: 4.12s                   │
└──────────────────────────────────────────────────────────────┘
```

### Settings Tab (配置管理)

```
┌──────────────────────────────────────────────────────────────┐
│  🔧 MCP Server Configuration                                 │
├──────────────────────────────────────────────────────────────┤
│  Houdini Path:                                               │
│  [C:/Program Files/Side Effects Software/...]  [Browse]      │
│                                                              │
│  Timeout Settings:                                           │
│    Default Timeout:     [30] seconds                         │
│    Create Box:          [15] seconds                         │
│    Polyreduce:          [30] seconds                         │
│    Boolean:             [45] seconds                         │
│    Import Geometry:     [60] seconds                         │
│                                                              │
│  Logging:                                                    │
│    Log Level: [INFO ▼]  (DEBUG, INFO, WARNING, ERROR)        │
│    ☑ Enable File Logging                                    │
│    ☑ Enable Console Logging                                 │
│    Log Path: [C:/Users/wepie/.claude/logs]  [Browse]        │
│                                                              │
│  Performance:                                                │
│    ☑ Enable Operation Cache                                 │
│    ☑ Auto-reconnect on Failure                              │
│    Max Retry Attempts: [3]                                   │
│                                                              │
│  [Apply Changes] [Restart with New Config] [Reset Defaults] │
└──────────────────────────────────────────────────────────────┘
```

### Logs Tab (实时日志)

```
┌──────────────────────────────────────────────────────────────┐
│  🔍 Filter: [All Levels ▼] [Search: ________]  [Clear Logs]  │
├──────────────────────────────────────────────────────────────┤
│  [12:30:45] [INFO] Server started successfully               │
│  [12:30:46] [INFO] WebSocket server listening on :9876       │
│  [12:31:02] [INFO] Tool called: create_box                   │
│  [12:31:02] [DEBUG] Parameters: {node_name: 'box1', ...}     │
│  [12:31:02] [INFO] Execution time: 0.23s                     │
│  [12:31:50] [ERROR] mirror operation timeout after 30s       │
│  [12:31:50] [WARNING] Killing process PID 12345              │
│  [12:32:15] [INFO] Tool called: boolean                      │
│  ▼ (Auto-scroll to bottom)                                   │
└──────────────────────────────────────────────────────────────┘

右键菜单:
  - Copy Line
  - Copy All
  - Export to File
  - Highlight Errors
```

---

## 🔌 WebSocket Protocol

### GUI → MCP Server 控制命令

```json
// 重启Houdini连接
{
  "command": "restart_houdini",
  "params": {}
}

// 重新加载配置
{
  "command": "reload_config",
  "params": {
    "config_path": "C:/Users/wepie/..."
  }
}

// 清空缓存
{
  "command": "clear_cache",
  "params": {}
}

// 更新超时设置
{
  "command": "update_timeout",
  "params": {
    "operation": "polyreduce",
    "timeout": 60.0
  }
}
```

### MCP Server → GUI 状态推送

```json
// 服务器状态更新
{
  "type": "status_update",
  "data": {
    "server_running": true,
    "uptime_seconds": 9255,
    "houdini_connected": true,
    "houdini_pid": 26760
  }
}

// 操作记录
{
  "type": "operation_log",
  "data": {
    "timestamp": "2026-03-16T12:31:02Z",
    "operation": "create_box",
    "status": "success",
    "duration": 0.23,
    "params": {...},
    "result": {...}
  }
}

// 日志消息
{
  "type": "log_message",
  "data": {
    "level": "INFO",
    "message": "Tool called: create_box",
    "timestamp": "2026-03-16T12:31:02Z"
  }
}

// 性能指标
{
  "type": "performance_metrics",
  "data": {
    "total_operations": 127,
    "success_rate": 0.976,
    "avg_response_time": 0.87,
    "p95_response_time": 2.34
  }
}
```

---

## 🚀 实现计划

### Phase 1: 核心架构 (Day 1-2)

1. **MCP Server增强**
   - 添加WebSocket Server (websockets库)
   - 实现HoudiniConnectionManager (可热重启)
   - 分离FastMCP和连接管理层

2. **基础GUI (PyQt6)**
   - 主窗口框架
   - Dashboard基础界面
   - WebSocket客户端连接

### Phase 2: 功能完善 (Day 3-4)

1. **监控功能**
   - 实时状态显示
   - 操作历史记录
   - 日志实时显示

2. **控制功能**
   - 重启按钮（热重启）
   - 配置修改界面
   - 手动操作触发

### Phase 3: 高级功能 (Day 5-6)

1. **性能监控**
   - 实时图表 (pyqtgraph)
   - 统计分析
   - 导出报告

2. **场景预览**
   - 节点树显示
   - 几何体预览 (需要Houdini Engine)

3. **体验优化**
   - 托盘图标
   - 通知提醒
   - 快捷键支持

### Phase 4: 打包发布 (Day 7)

1. **打包**
   - PyInstaller打包成exe
   - 自动启动脚本
   - 安装向导

2. **文档**
   - 用户手册
   - API文档
   - 故障排查指南

---

## 📦 技术栈

### 后端
- **Python 3.11**
- **FastMCP** - MCP协议处理
- **websockets** - WebSocket服务器
- **asyncio** - 异步处理

### 前端
- **PyQt6** - GUI框架
- **pyqtgraph** - 实时图表
- **qasync** - Qt + asyncio集成

### 打包
- **PyInstaller** - 打包成exe
- **NSIS** - 安装程序

---

## 🎯 最终效果

**用户体验**：

1. 双击启动 `Houdini MCP Control Panel.exe`
2. GUI窗口弹出，显示"Starting MCP Server..."
3. 几秒后状态变为"● Running"
4. Claude Code自动连接到MCP Server
5. 所有Houdini操作正常工作

**需要重启Houdini时**：

1. 在GUI中点击 [Restart Houdini]
2. 几秒后完成重启
3. Claude Code无感知，继续正常工作
4. **无需重启Claude Code** ✅

**配置修改时**：

1. 在Settings Tab修改超时时间
2. 点击 [Apply Changes]
3. 立即生效
4. **无需重启任何进程** ✅

---

## 🔐 安全性

- WebSocket只监听localhost (127.0.0.1)
- 不暴露到外网
- 可选添加Token认证

---

## 📝 Notes

- GUI作为独立进程，崩溃不影响MCP Server
- MCP Server崩溃会自动重启（由Claude Code管理）
- 所有状态持久化到SQLite数据库
- 支持多实例检测（防止重复启动）

---

## 🎨 UI Theme

- **Dark Mode** (默认)
- **Light Mode** (可选)
- 遵循系统主题
- 自定义配色方案

---

**准备开始实现！** 🚀
