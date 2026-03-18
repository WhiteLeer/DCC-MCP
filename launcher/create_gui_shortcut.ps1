# 创建Houdini MCP GUI的桌面快捷方式

$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $Desktop "MCP控制面板.lnk"
$TargetPath = "C:\Users\wepie\houdini-mcp\启动GUI.bat"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = "C:\Users\wepie\houdini-mcp"
$Shortcut.Description = "Houdini MCP 控制面板 - 监控和管理MCP服务器"

# 使用Python图标（如果有）或系统图标
$PythonPath = "C:\Program Files\Python311\python.exe"
if (Test-Path $PythonPath) {
    $Shortcut.IconLocation = "$PythonPath,0"
}

$Shortcut.Save()

Write-Host "✅ 桌面快捷方式创建成功：$ShortcutPath" -ForegroundColor Green
Write-Host ""
Write-Host "双击'MCP控制面板.lnk'即可启动GUI" -ForegroundColor Cyan
