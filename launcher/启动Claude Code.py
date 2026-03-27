"""
Claude Code 智能启动器
- 普通模式：可多开
- 每种 MCP 模式：单实例限制（通过锁文件检测）
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import json
import os
import time
import threading
from pathlib import Path

# Claude Code 插件配置路径
CLAUDE_DIR = Path.home() / ".claude"
PLUGIN_DIR = CLAUDE_DIR / "plugins" / "houdini-mcp"
PLUGIN_CONFIG = PLUGIN_DIR / ".claude-plugin" / "plugin.json"

# 锁文件路径
HOUDINI_LOCK_FILE = PLUGIN_DIR / ".running.lock"

# 普通模式实例计数文件
NORMAL_COUNTER_FILE = CLAUDE_DIR / ".normal_instance_counter"

# Claude Code可执行文件路径
CLAUDE_PATHS = [
    Path.home() / ".local" / "bin" / "claude.exe",  # 实际安装路径 ⭐
    Path(os.getenv("LOCALAPPDATA")) / "Programs" / "claude-code" / "Claude Code.exe",
    Path(os.getenv("PROGRAMFILES")) / "Claude Code" / "Claude Code.exe",
    Path(os.getenv("PROGRAMFILES(X86)")) / "Claude Code" / "Claude Code.exe",
]


def is_houdini_mcp_running() -> bool:
    """检查 Houdini MCP 是否正在运行（通过锁文件）"""
    return HOUDINI_LOCK_FILE.exists()


def get_next_normal_instance_number() -> int:
    """获取下一个普通模式实例编号"""
    try:
        if NORMAL_COUNTER_FILE.exists():
            counter = int(NORMAL_COUNTER_FILE.read_text().strip())
        else:
            counter = 0

        # 递增并保存
        next_number = counter
        NORMAL_COUNTER_FILE.write_text(str(counter + 1))
        return next_number
    except:
        return 0


def set_window_title(target_pid: int, new_title: str, max_wait: int = 15):
    """
    修改指定进程的 Claude Code 窗口标题

    Args:
        target_pid: 目标进程 PID
        new_title: 新标题
        max_wait: 最大等待时间（秒）
    """
    def _set_title():
        try:
            import win32gui
            import win32process

            # 等待窗口出现
            for attempt in range(max_wait * 2):  # 每0.5秒检查一次
                time.sleep(0.5)

                # 查找目标进程的窗口
                def callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                        if window_pid == target_pid:
                            title = win32gui.GetWindowText(hwnd)
                            # 查找主窗口（有标题的窗口）
                            if title:
                                windows.append(hwnd)
                    return True

                windows = []
                win32gui.EnumWindows(callback, windows)

                if windows:
                    # 修改找到的窗口标题
                    for hwnd in windows:
                        old_title = win32gui.GetWindowText(hwnd)
                        if old_title and ('claude' in old_title.lower() or 'code' in old_title.lower()):
                            win32gui.SetWindowText(hwnd, new_title)
                            print(f"✓ 窗口标题已修改：{old_title} → {new_title}")
                            return True

            print(f"⚠ 未能在 {max_wait} 秒内找到窗口（PID: {target_pid}）")
            return False

        except ImportError:
            # 如果没有 pywin32，忽略标题设置
            print("⚠ pywin32 未安装，跳过窗口标题设置")
            return False
        except Exception as e:
            print(f"⚠ 设置窗口标题失败：{e}")
            return False

    # 在后台线程中执行，不阻塞主程序
    thread = threading.Thread(target=_set_title, daemon=True)
    thread.start()


def find_claude_executable() -> Path | None:
    """查找Claude Code可执行文件"""
    for path in CLAUDE_PATHS:
        if path.exists():
            return path
    return None


def enable_houdini_plugin(enable: bool):
    """启用或禁用 Houdini MCP 插件"""
    try:
        # 确保插件配置存在
        if not PLUGIN_CONFIG.exists():
            messagebox.showerror(
                "插件未安装",
                f"Houdini MCP 插件配置不存在:\n{PLUGIN_CONFIG}\n\n"
                "请先安装插件。"
            )
            return False

        # 读取插件配置
        with open(PLUGIN_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 修改启用状态
        config['enabled'] = enable

        # 保存配置
        with open(PLUGIN_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        messagebox.showerror("配置失败", f"无法修改插件配置:\n{e}")
        return False


def launch_claude(use_mcp: bool, window_title: str = None):
    """启动Claude Code

    Args:
        use_mcp: 是否启用 MCP 模式
        window_title: 自定义窗口标题（可选）
    """
    # 修改插件启用状态
    if not enable_houdini_plugin(use_mcp):
        return

    # 查找可执行文件
    claude_exe = find_claude_executable()
    if not claude_exe:
        messagebox.showerror(
            "找不到Claude Code",
            "无法找到Claude Code可执行文件。\n\n请检查安装路径：\n" +
            "\n".join(str(p) for p in CLAUDE_PATHS)
        )
        return

    # 启动
    try:
        # 启动进程并获取 PID
        process = subprocess.Popen([str(claude_exe)], shell=False)
        new_pid = process.pid

        # 如果指定了窗口标题，在后台修改
        if window_title:
            set_window_title(new_pid, window_title)

        # 提示用户
        if use_mcp:
            messagebox.showinfo(
                "启动成功",
                f"Claude Code 已启动（PID: {new_pid}）\n"
                f"窗口标题：{window_title or 'Claude Code'}\n\n"
                "请在 Claude Code 中：\n"
                "1. 等待插件加载完成\n"
                "2. 打开 Houdini MCP Control GUI\n"
                "3. 开始使用 Houdini 工具"
            )
        else:
            messagebox.showinfo(
                "启动成功",
                f"Claude Code 已启动（PID: {new_pid}）\n"
                f"窗口标题：{window_title or 'Claude Code'}\n\n"
                "MCP 插件已禁用"
            )

        root.destroy()

    except Exception as e:
        messagebox.showerror("启动失败", f"无法启动Claude Code:\n{e}")


class LauncherWindow:
    """启动器窗口"""

    def __init__(self, master):
        self.master = master
        master.title("Claude Code 启动器")
        master.geometry("450x320")
        master.resizable(False, False)

        # 检查 Houdini MCP 是否正在运行（锁文件检测）
        self.houdini_mcp_running = is_houdini_mcp_running()

        # 检查插件是否已安装
        self.plugin_installed = PLUGIN_CONFIG.exists()

        # 标题
        title_label = tk.Label(
            master,
            text="⚙️ Claude Code 启动器",
            font=("微软雅黑", 18, "bold"),
            pady=20
        )
        title_label.pack()

        # 状态提示
        if not self.plugin_installed:
            status_text = "⚠️ Houdini MCP 插件未安装"
            status_color = "orange"
        elif self.houdini_mcp_running:
            status_text = "⚠️ Houdini MCP 已有实例运行（锁文件检测）"
            status_color = "orange"
        else:
            status_text = "✅ 就绪，可以启动"
            status_color = "green"

        status_label = tk.Label(
            master,
            text=status_text,
            font=("微软雅黑", 10),
            fg=status_color,
            pady=10
        )
        status_label.pack()

        # 说明
        info_text = "请选择启动模式："
        info_label = tk.Label(
            master,
            text=info_text,
            font=("微软雅黑", 10),
            pady=10
        )
        info_label.pack()

        # 按钮框架
        button_frame = tk.Frame(master)
        button_frame.pack(pady=20)

        # MCP模式按钮
        mcp_btn_text = "🎨 Houdini MCP 模式"
        if self.houdini_mcp_running:
            mcp_btn_text += "\n（已有实例运行）"
        elif not self.plugin_installed:
            mcp_btn_text += "\n（插件未安装）"

        mcp_enabled = self.plugin_installed and not self.houdini_mcp_running
        self.mcp_button = tk.Button(
            button_frame,
            text=mcp_btn_text,
            font=("微软雅黑", 11, "bold"),
            width=18,
            height=3,
            bg="#3498db" if mcp_enabled else "#95a5a6",
            fg="white",
            command=self.launch_mcp_mode,
            state=tk.NORMAL if mcp_enabled else tk.DISABLED
        )
        self.mcp_button.pack(side=tk.LEFT, padx=10)

        # 普通模式按钮 - 永远可用！
        normal_button = tk.Button(
            button_frame,
            text="📝 普通模式\n（禁用MCP，可多开）",
            font=("微软雅黑", 11, "bold"),
            width=18,
            height=3,
            bg="#2ecc71",
            fg="white",
            command=self.launch_normal_mode
        )
        normal_button.pack(side=tk.LEFT, padx=10)

        # 底部提示
        if not self.plugin_installed:
            hint_text = "⚠️ 插件未安装，请先安装插件\nMCP模式：每种工具单实例\n普通模式：可多开，自动编号"
            hint_color = "orange"
        else:
            hint_text = "MCP模式：每种工具单实例（锁文件检测）\n普通模式：可多开，窗口标题自动编号（普通-0、普通-1...）"
            hint_color = "gray"

        hint_label = tk.Label(
            master,
            text=hint_text,
            font=("微软雅黑", 8),
            fg=hint_color,
            pady=10
        )
        hint_label.pack()

    def launch_mcp_mode(self):
        """启动 Houdini MCP 模式"""
        # 再次检查锁文件（防止在GUI打开期间启动）
        if is_houdini_mcp_running():
            messagebox.showwarning(
                "Houdini MCP 已运行",
                "检测到 Houdini MCP 锁文件存在。\n\n"
                "已有 Houdini MCP 实例在运行，请：\n"
                "1. 关闭正在使用 Houdini MCP 的 Claude Code 窗口\n"
                "2. 或在 Houdini MCP GUI 中点击'清理旧进程'\n\n"
                f"锁文件位置：{HOUDINI_LOCK_FILE}\n\n"
                "提示：普通模式不受此限制，可多开"
            )
            return

        if not self.plugin_installed:
            messagebox.showerror(
                "插件未安装",
                "Houdini MCP 插件尚未安装。\n\n"
                "请先安装插件。"
            )
            return

        result = messagebox.askyesno(
            "启动 Houdini MCP 模式",
            "将启动 Houdini MCP 模式。\n\n"
            "✅ 自动启用 Houdini MCP 插件\n"
            "✅ 窗口标题：Claude-Houdini MCP\n"
            "✅ 启动后请打开 Houdini MCP Control GUI\n"
            "⚠️ 单实例限制：同一时间只能运行1个 Houdini MCP\n\n"
            "继续？"
        )

        if result:
            launch_claude(use_mcp=True, window_title="Claude-Houdini MCP")

    def launch_normal_mode(self):
        """启动普通模式 - 可多开"""
        # 获取下一个实例编号
        instance_number = get_next_normal_instance_number()
        window_title = f"Claude-普通-{instance_number}"

        result = messagebox.askyesno(
            "启动普通模式",
            f"将启动普通模式（禁用 MCP 插件）。\n\n"
            f"✅ 窗口标题：{window_title}\n"
            "✅ 可多开：没有实例数量限制\n"
            "✅ 每个窗口独立运行\n\n"
            "继续？"
        )

        if result:
            launch_claude(use_mcp=False, window_title=window_title)


if __name__ == "__main__":
    root = tk.Tk()
    app = LauncherWindow(root)
    root.mainloop()


