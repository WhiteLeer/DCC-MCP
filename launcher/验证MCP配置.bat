@echo off
chcp 65001 > nul
echo ============================================
echo    Houdini MCP 配置验证工具
echo ============================================
echo.

echo [1/4] 检查全局配置...
if exist "%USERPROFILE%\.claude\mcp.json" (
    echo ❌ 警告: 全局配置存在，会导致双实例！
    echo    位置: %USERPROFILE%\.claude\mcp.json
    echo    建议: 删除此文件
) else (
    echo ✅ 全局配置不存在（正确）
)
echo.

echo [2/4] 检查插件配置...
if exist "%USERPROFILE%\.claude\plugins\houdini-mcp\.mcp.json" (
    echo ✅ 插件MCP配置存在
    type "%USERPROFILE%\.claude\plugins\houdini-mcp\.mcp.json"
) else (
    echo ❌ 插件MCP配置不存在！
)
echo.

echo [3/4] 检查plugin.json...
if exist "%USERPROFILE%\.claude\plugins\houdini-mcp\.claude-plugin\plugin.json" (
    echo ✅ plugin.json存在
    type "%USERPROFILE%\.claude\plugins\houdini-mcp\.claude-plugin\plugin.json"
) else (
    echo ❌ plugin.json不存在！
)
echo.

echo [4/4] 检查端口占用...
netstat -ano | findstr ":9876" > nul
if %errorlevel% equ 0 (
    echo ⚠️ 端口9876已被占用（MCP可能正在运行）
    netstat -ano | findstr ":9876"
) else (
    echo ✅ 端口9876空闲（可以启动MCP）
)
echo.

echo ============================================
echo    检查完成
echo ============================================
echo.
echo 如果发现问题，请查看: 系统诊断报告.md
echo.
pause
