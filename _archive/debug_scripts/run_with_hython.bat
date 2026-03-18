@echo off
REM Houdini MCP Server launcher using hython

set HOUDINI_BIN=C:\Program Files\Side Effects Software\Houdini 20.5.487\bin
set HYTHON=%HOUDINI_BIN%\hython.exe

echo ==================================================
echo Starting Houdini MCP Server with hython
echo ==================================================
echo Houdini bin: %HOUDINI_BIN%
echo Python: %HYTHON%
echo ==================================================

REM Install dependencies in hython
echo Installing MCP dependencies...
"%HYTHON%" -m pip install mcp dcc-mcp-core --quiet

REM Run the server
"%HYTHON%" -m houdini_mcp.server %*
