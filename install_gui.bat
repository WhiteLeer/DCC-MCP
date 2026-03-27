@echo off
echo ========================================
echo Houdini MCP GUI Installation
echo ========================================
echo.

echo [1/3] Installing GUI dependencies...
pip install -r requirements_gui.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo [2/3] Updating Claude Code configuration...
python -c "import json, os; config_path = os.path.expanduser('~/AppData/Roaming/Claude/claude_desktop_config.json'); config = json.load(open(config_path)) if os.path.exists(config_path) else {'mcpServers': {}}; config['mcpServers']['houdini'] = {'command': 'C:/Program Files/Side Effects Software/Houdini 20.5.487/bin/hython.exe', 'args': ['-m', 'houdini_mcp.server_with_gui'], 'env': {'HOUDINI_PATH': 'C:/Program Files/Side Effects Software/Houdini 20.5.487/bin', 'PYTHONPATH': 'C:/Users/wepie/dcc-mcp'}}; json.dump(config, open(config_path, 'w'), indent=2)"
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Could not update config automatically
    echo Please manually update: %USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json
)
echo.

echo [3/3] Installation complete!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Restart Claude Code
echo 2. Run: python run_gui.py
echo 3. Enjoy hot-reloadable MCP!
echo ========================================
echo.
pause

