@echo off
title Houdini MCP Daemon

cd /d "%~dp0"
python -m houdini_mcp.daemon_server
