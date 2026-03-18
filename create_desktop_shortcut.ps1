# Create Desktop Shortcut for Houdini MCP GUI

$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $DesktopPath "Houdini MCP Control.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "C:\Windows\System32\cmd.exe"
$Shortcut.Arguments = "/c `"cd /d C:\Users\wepie\houdini-mcp && python run_gui.py`""
$Shortcut.WorkingDirectory = "C:\Users\wepie\houdini-mcp"
$Shortcut.Description = "Houdini MCP Professional Control Panel"
$Shortcut.IconLocation = "C:\Windows\System32\shell32.dll,21"
$Shortcut.Save()

Write-Host "✅ Desktop shortcut created: $ShortcutPath" -ForegroundColor Green
Write-Host ""
Write-Host "You can now double-click 'Houdini MCP Control' on your desktop!" -ForegroundColor Cyan
Write-Host ""
pause
