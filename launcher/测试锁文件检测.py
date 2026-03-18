"""
测试 Houdini MCP 锁文件检测逻辑
"""

from pathlib import Path

# 锁文件路径
HOUDINI_LOCK_FILE = Path.home() / ".claude" / "plugins" / "houdini-mcp" / ".running.lock"

def is_houdini_mcp_running() -> bool:
    """检查 Houdini MCP 是否正在运行（通过锁文件）"""
    return HOUDINI_LOCK_FILE.exists()

if __name__ == "__main__":
    print("=" * 60)
    print("  Houdini MCP 锁文件检测测试")
    print("=" * 60)
    print()
    print(f"锁文件路径：{HOUDINI_LOCK_FILE}")
    print()

    is_running = is_houdini_mcp_running()

    if is_running:
        print("✓ 锁文件存在 → Houdini MCP 正在运行")
        print()
        print("启动器行为：")
        print("  - 'Houdini MCP 模式' 按钮将被禁用")
        print("  - 普通模式仍可启动（不受影响）")
        print()
        try:
            content = HOUDINI_LOCK_FILE.read_text()
            print("锁文件内容：")
            print(content)
        except:
            pass
    else:
        print("✗ 锁文件不存在 → Houdini MCP 未运行")
        print()
        print("启动器行为：")
        print("  - 'Houdini MCP 模式' 按钮可用")
        print("  - 可以启动新的 Houdini MCP 实例")

    print()
    print("=" * 60)
    print("工作原理：")
    print("=" * 60)
    print("1. Houdini MCP 启动时创建锁文件")
    print("2. Houdini MCP 关闭时删除锁文件")
    print("3. 启动器检查锁文件来判断是否已运行")
    print("4. 优势：不受端口自动顺延影响，检测准确")
    print()
    print("注意事项：")
    print("- 如果 MCP 异常崩溃，锁文件可能残留")
    print("- 可以手动删除残留的锁文件")
    print()
    input("按回车键退出...")
