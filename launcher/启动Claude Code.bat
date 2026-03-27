@echo off
REM Claude Code 智能启动器
REM 自动选择是否启用Houdini MCP

cd /d "%~dp0"
python "启动Claude Code.py"

if errorlevel 1 (
    echo.
    echo 错误：Python未安装或脚本执行失败
    echo 请确保已安装Python 3.8+
    pause
)


