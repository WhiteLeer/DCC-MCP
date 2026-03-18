# 集成到Claude Code

## 📋 步骤1：配置Claude Code

### Windows配置文件位置
```
%APPDATA%/Claude/claude_desktop_config.json
```

完整路径：
```
C:/Users/wepie/AppData/Roaming/Claude/claude_desktop_config.json
```

### 配置内容

打开或创建该文件，添加以下内容：

```json
{
  "mcpServers": {
    "houdini": {
      "command": "C:/Program Files/Side Effects Software/Houdini 20.5.487/bin/hython.exe",
      "args": [
        "-m",
        "houdini_mcp.server"
      ],
      "env": {
        "HOUDINI_PATH": "C:/Program Files/Side Effects Software/Houdini 20.5.487/bin"
      }
    }
  }
}
```

**注意**：如果文件中已有其他MCP Server配置，只需在 `mcpServers` 对象中添加 `"houdini"` 部分。

---

## 🔧 步骤2：重启Claude Code

1. 完全关闭Claude Code
2. 重新打开Claude Code
3. 等待MCP Server自动连接（首次启动可能需要10-15秒）

---

## ✅ 步骤3：验证连接

在Claude Code中输入：

```
列出所有可用的Houdini工具
```

如果成功，应该看到：
- `create_box` - 创建盒子几何
- `polyreduce` - 减少多边形
- `list_actions` - 列出所有Action
- `execute_action` - 执行任意Action
- `get_scene_state` - 获取场景状态

---

## 🎯 测试用例

### 测试用例1：创建简单几何
```
用Houdini创建一个2x2x2的盒子，命名为test_box
```

### 测试用例2：减面操作
```
把/obj/test_box减面到50%
```

### 测试用例3：批量创建
```
用Houdini创建3个盒子：
- small_box: 1x1x1
- medium_box: 2x2x2
- large_box: 3x3x3
```

### 测试用例4：完整Pipeline
```
用Houdini执行以下操作：
1. 创建一个5x3x2的盒子，命名为pipeline_test
2. 将它减面到25%
3. 查询当前场景有多少个节点
```

### 测试用例5：查询信息
```
查询当前Houdini场景的状态，告诉我有哪些节点
```

### 测试用例6：复杂组合
```
帮我在Houdini中：
1. 创建一个名为cube_a的2x2x2盒子
2. 创建一个名为cube_b的3x3x3盒子
3. 分别把它们减面到不同的比例（cube_a减到30%，cube_b减到50%）
4. 告诉我最终每个盒子有多少多边形
```

---

## 🔍 故障排查

### 问题1：MCP Server没有出现在工具列表

**检查**：
1. 确认配置文件路径正确
2. 确认JSON格式正确（使用JSONLint验证）
3. 查看Claude Code日志（菜单 → Help → Show Logs）

**解决**：
```bash
# 检查hython是否正常
"C:/Program Files/Side Effects Software/Houdini 20.5.487/bin/hython.exe" --version

# 测试MCP Server是否能启动
"C:/Program Files/Side Effects Software/Houdini 20.5.487/bin/hython.exe" -m houdini_mcp.server --help
```

### 问题2：工具调用失败

**检查日志**：
Claude Code会显示详细的错误信息，包括：
- Houdini初始化失败
- Action执行错误
- 参数验证失败

**常见错误**：
- `Node not found` → 节点路径错误，使用 `get_scene_state` 查看正确路径
- `'hou' module not available` → Context传递问题（已修复，不应该出现）
- `Geometry object has no attribute` → Houdini API版本问题

### 问题3：Houdini路径错误

如果Houdini安装在其他位置，修改配置文件中的路径：

```json
{
  "mcpServers": {
    "houdini": {
      "command": "你的Houdini路径/bin/hython.exe",
      "args": ["-m", "houdini_mcp.server"],
      "env": {
        "HOUDINI_PATH": "你的Houdini路径/bin"
      }
    }
  }
}
```

---

## 📊 高级用法

### 使用execute_action调用任意Action

```
使用execute_action工具，调用create_box，参数为：
{
  "node_name": "custom_box",
  "size_x": 4.0,
  "size_y": 4.0,
  "size_z": 4.0
}
```

### 查询可用的所有Actions

```
调用list_actions工具，告诉我所有可用的Houdini操作
```

### 组合使用Resources

```
读取 houdini://scene/state 资源，告诉我当前场景信息
```

---

## 🎓 理解MCP工作原理

```
你的对话
    ↓
Claude Code (AI)
    ↓ 识别需要调用Houdini工具
    ↓
MCP Protocol (JSON-RPC over Stdio)
    ↓
Houdini MCP Server (hython进程)
    ↓
ActionManager + Actions
    ↓
Houdini hou API
    ↓
返回结果给Claude
```

**特点**：
- 每次Claude启动时，MCP Server作为子进程运行
- 使用标准输入/输出(Stdio)通信
- Claude自动选择合适的工具
- 支持流式响应和错误处理

---

## 📝 配置文件备份

已创建配置模板：`C:/Users/wepie/houdini-mcp/claude_mcp_config.json`

手动复制到Claude配置目录：
```bash
copy "C:\Users\wepie\houdini-mcp\claude_mcp_config.json" "%APPDATA%\Claude\claude_desktop_config.json"
```

或合并到现有配置（如果已有其他MCP Server）。
