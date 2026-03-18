# 创建Claude Code启动器的桌面快捷方式

$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $Desktop "启动 Claude Code.lnk"
$LauncherDir = "C:\Users\wepie\houdini-mcp\launcher"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "pythonw.exe"  # 使用pythonw.exe避免命令行窗口
$Shortcut.Arguments = "`"$LauncherDir\启动Claude Code.py`""
$Shortcut.WorkingDirectory = $LauncherDir
$Shortcut.Description = "Claude Code 智能启动器 - 选择是否启用Houdini MCP"

# 尝试使用Claude Code图标（如果存在）
$ClaudePaths = @(
    "$env:LOCALAPPDATA\Programs\claude-code\Claude Code.exe",
    "$env:PROGRAMFILES\Claude Code\Claude Code.exe"
)

foreach ($path in $ClaudePaths) {
    if (Test-Path $path) {
        $Shortcut.IconLocation = "$path,0"
        break
    }
}

$Shortcut.Save()

Write-Host "✅ 桌面快捷方式创建成功：$ShortcutPath" -ForegroundColor Green
Write-Host ""
Write-Host "双击'启动 Claude Code.lnk'即可使用智能启动器" -ForegroundColor Cyan
