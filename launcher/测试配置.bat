@echo off
chcp 65001 >nul
title Claude Code MCP 配置测试

echo.
echo ========================================
echo   Claude Code MCP 配置测试
echo ========================================
echo.

python "%~dp0测试配置.py"

echo.
echo 按任意键退出...
pause >nul
