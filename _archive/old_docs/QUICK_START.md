# 🚀 快速开始指南

## ✅ 已完成的配置

我已经帮您完成了以下配置：

1. ✅ **安装依赖** - mcp, dcc-mcp-core
2. ✅ **创建项目** - houdini-mcp包
3. ✅ **实现Actions** - create_box, polyreduce
4. ✅ **配置Claude** - claude_desktop_config.json已创建

---

## 📋 现在您只需要3步

### 步骤1：验证配置（30秒）

双击运行：
```
C:\Users\wepie\houdini-mcp\verify_setup.bat
```

应该看到所有✅检查通过。

---

### 步骤2：重启Claude Code（1分钟）

1. 完全关闭当前Claude Code窗口
2. 重新打开Claude Code
3. 等待10-15秒（MCP Server初始化）

---

### 步骤3：测试（5分钟）

在Claude Code中输入：

```
检查Houdini MCP工具是否可用
```

如果成功，会看到类似：
```
✅ Houdini MCP Server已连接
可用工具：
- create_box: 创建盒子几何
- polyreduce: 减少多边形
- get_scene_state: 查询场景状态
- list_actions: 列出所有Action
- execute_action: 执行Action
```

---

## 🎯 测试用例（从简单到复杂）

### 🟢 Level 1：基础操作

**测试1**：
```
用Houdini创建一个2x2x2的盒子，命名为my_first_box
```

**测试2**：
```
把my_first_box减面到50%
```

**测试3**：
```
查询当前Houdini场景有哪些节点
```

---

### 🟡 Level 2：组合操作

**测试4**：
```
创建3个盒子：small(1x1x1), medium(2x2x2), large(3x3x3)
```

**测试5**：
```
创建一个5x3x2的盒子，然后减面到25%，告诉我最终有多少多边形
```

---

### 🔴 Level 3：复杂任务

**测试6**：
```
帮我做这些：
1. 创建box_a(2x2x2)和box_b(3x3x3)
2. box_a减到30%，box_b减到70%
3. 生成报告：每个盒子原始和减面后的多边形数
```

---

## 📊 配置文件位置

所有重要文件：

```
C:\Users\wepie\houdini-mcp\
├── houdini_mcp/              # 项目代码
│   ├── server.py             # MCP Server
│   ├── adapter/              # Houdini适配器
│   └── actions/sop/          # SOP操作
│       ├── create_box.py
│       └── polyreduce.py
├── SETUP_CLAUDE.md           # 详细设置指南
├── TEST_CASES.md             # 完整测试用例
├── verify_setup.bat          # 验证脚本
└── claude_mcp_config.json    # 配置模板
```

**Claude配置文件**：
```
C:\Users\wepie\AppData\Roaming\Claude\claude_desktop_config.json
```

---

## 🔍 故障排查

### 问题1：工具没有出现

**解决**：
1. 检查 `verify_setup.bat` 的输出
2. 重启Claude Code
3. 查看Claude日志（Help → Show Logs）

**常见原因**：
- JSON格式错误
- hython路径不对
- 首次加载需要时间

---

### 问题2：调用失败

**解决**：
```
先用"查询Houdini场景状态"确认连接正常
```

**检查**：
- 节点路径是否正确（用get_scene_state查看）
- 参数是否符合要求（大小>0等）

---

### 问题3：权限问题

如果提示"无法写入配置文件"：
```bash
# 以管理员身份运行
cd C:\Users\wepie\houdini-mcp
verify_setup.bat
```

---

## 💡 工作原理

```
你在Claude Code输入
    ↓
"用Houdini创建一个盒子"
    ↓
Claude识别需要调用Houdini工具
    ↓
MCP Protocol (JSON-RPC)
    ↓
Houdini MCP Server (hython进程)
    ↓
ActionManager调用create_box Action
    ↓
Houdini hou API创建节点
    ↓
返回结果（节点路径、多边形数等）
    ↓
Claude生成自然语言回复
```

**关键**：
- 自动启动：Claude Code启动时自动运行hython
- Stdio通信：标准输入输出，不需要网络
- 类型安全：Pydantic验证所有参数
- 优雅降级：如果失败会返回清晰错误

---

## 🎓 进阶使用

### 添加新Action

1. 在 `houdini_mcp/actions/sop/` 创建新文件
2. 继承 `Action` 类
3. 定义 `InputModel` 和 `OutputModel`
4. 实现 `_execute()` 方法
5. 重启Claude Code（自动加载）

**示例**：见 `create_box.py` 和 `polyreduce.py`

### 查看可用Actions

```
调用list_actions，显示所有Houdini操作
```

### 直接调用execute_action

```
使用execute_action工具执行polyreduce，参数：
{
  "geo_path": "/obj/my_box",
  "target_percent": 30.0
}
```

---

## 📚 文档

- **SETUP_CLAUDE.md** - 详细配置说明
- **TEST_CASES.md** - 10个测试用例
- **STATUS.md** - 项目状态和架构
- **README.md** - 项目说明

---

## ✅ 配置检查清单

- [ ] hython可以运行
- [ ] houdini-mcp已安装
- [ ] claude_desktop_config.json已创建
- [ ] Claude Code已重启
- [ ] 测试1通过（创建盒子）
- [ ] 测试2通过（减面）
- [ ] 测试3通过（查询状态）

**全部✅后，您就可以用自然语言控制Houdini了！**

---

## 🎉 恭喜！

您现在拥有了：
- ✅ AI驱动的Houdini工作流
- ✅ 类型安全的Action系统
- ✅ 可扩展的架构（方便添加新功能）
- ✅ 优雅的错误处理

**开始享受吧！** 🚀

有问题随时问我，我会帮您调试和扩展功能。
