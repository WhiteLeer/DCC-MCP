"""
测试 Claude Code MCP 配置是否正确
"""
import json
from pathlib import Path

# 配置路径
PLUGIN_CONFIG = Path.home() / ".claude" / "plugins" / "houdini-mcp" / ".claude-plugin" / "plugin.json"
MCP_CONFIG = Path.home() / ".claude" / "plugins" / "houdini-mcp" / ".mcp.json"

print("=" * 60)
print("Claude Code MCP 配置检查")
print("=" * 60)

# 检查插件配置
print("\n1. 检查插件配置:")
print(f"   路径: {PLUGIN_CONFIG}")
if PLUGIN_CONFIG.exists():
    print("   ✅ 文件存在")
    with open(PLUGIN_CONFIG, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(f"   插件名称: {config.get('name')}")
    print(f"   启用状态: {config.get('enabled')}")
    print(f"   MCP配置: {config.get('mcpConfig')}")
else:
    print("   ❌ 文件不存在")

# 检查 MCP 服务器配置
print("\n2. 检查 MCP 服务器配置:")
print(f"   路径: {MCP_CONFIG}")
if MCP_CONFIG.exists():
    print("   ✅ 文件存在")
    with open(MCP_CONFIG, 'r', encoding='utf-8') as f:
        mcp = json.load(f)
    servers = mcp.get('mcpServers', {})
    print(f"   服务器数量: {len(servers)}")
    for name, cfg in servers.items():
        print(f"   - {name}:")
        print(f"     命令: {cfg.get('command')}")
        print(f"     参数: {cfg.get('args')}")
else:
    print("   ❌ 文件不存在")

# 检查 Claude Desktop 配置（应该不存在）
print("\n3. 检查 Claude Desktop 配置:")
desktop_config = Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
if desktop_config.exists():
    print(f"   ⚠️ 文件存在: {desktop_config}")
    print("   （应该删除此文件，只使用 Claude Code）")
else:
    print("   ✅ 文件不存在（正确）")

print("\n" + "=" * 60)
print("总结:")
if PLUGIN_CONFIG.exists() and MCP_CONFIG.exists() and not desktop_config.exists():
    print("✅ 配置完整且正确！")
    print("\n下一步：")
    print("1. 双击 '启动Claude Code.bat'")
    print("2. 选择 'MCP 模式' 或 '普通模式'")
    print("3. 如果选择 MCP 模式，启动 'Houdini MCP Control' GUI")
else:
    print("⚠️ 配置存在问题，请检查上述输出")
print("=" * 60)
