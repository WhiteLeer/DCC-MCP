@echo off
REM Test Houdini MCP with hython

set HOUDINI_BIN=C:\Program Files\Side Effects Software\Houdini 20.5.487\bin
set HYTHON=%HOUDINI_BIN%\hython.exe

echo ==================================================
echo Testing Houdini MCP with hython
echo ==================================================

REM Install dependencies
echo Installing dependencies...
"%HYTHON%" -m pip install mcp dcc-mcp-core --quiet --disable-pip-version-check

REM Install houdini-mcp in editable mode
echo Installing houdini-mcp...
cd /d "%~dp0"
"%HYTHON%" -m pip install -e . --quiet --disable-pip-version-check

REM Run test
echo.
echo Running tests...
echo.
"%HYTHON%" test_basic.py

pause
