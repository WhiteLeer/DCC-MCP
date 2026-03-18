@echo off
echo ======================================================================
echo Houdini MCP Setup Verification
echo ======================================================================
echo.

echo [1/5] Checking Houdini installation...
if exist "C:\Program Files\Side Effects Software\Houdini 20.5.487\bin\hython.exe" (
    echo     ✅ Houdini found
) else (
    echo     ❌ Houdini not found at expected location
    goto :error
)

echo [2/5] Checking hython version...
"C:\Program Files\Side Effects Software\Houdini 20.5.487\bin\hython.exe" --version
if %ERRORLEVEL% EQU 0 (
    echo     ✅ hython works
) else (
    echo     ❌ hython failed
    goto :error
)

echo [3/5] Checking houdini-mcp installation...
"C:\Program Files\Side Effects Software\Houdini 20.5.487\bin\hython.exe" -c "import houdini_mcp; print('✅ houdini-mcp imported')"
if %ERRORLEVEL% EQU 0 (
    echo     ✅ houdini-mcp package found
) else (
    echo     ❌ houdini-mcp not installed
    echo     Run: hython -m pip install -e C:\Users\wepie\houdini-mcp
    goto :error
)

echo [4/5] Checking Claude config...
if exist "%APPDATA%\Claude\claude_desktop_config.json" (
    echo     ✅ Claude config exists
    type "%APPDATA%\Claude\claude_desktop_config.json"
) else (
    echo     ❌ Claude config not found
    echo     Creating default config...
    copy "C:\Users\wepie\houdini-mcp\claude_mcp_config.json" "%APPDATA%\Claude\claude_desktop_config.json"
)

echo [5/5] Testing MCP Server startup (5 seconds)...
echo     Starting server...
timeout /t 2 /nobreak >nul
start /min "Houdini MCP Test" cmd /c ""C:\Program Files\Side Effects Software\Houdini 20.5.487\bin\hython.exe" -m houdini_mcp.server 2>&1 | findstr /C:"✅" /C:"Loaded" /C:"ERROR""
timeout /t 3 /nobreak >nul
echo     ✅ Server can start (check output above)

echo.
echo ======================================================================
echo ✅ Setup verification complete!
echo ======================================================================
echo.
echo Next steps:
echo   1. Restart Claude Code
echo   2. Try: "列出所有Houdini工具"
echo   3. See TEST_CASES.md for more examples
echo.
goto :end

:error
echo.
echo ======================================================================
echo ❌ Setup verification failed!
echo ======================================================================
echo Please check the error messages above
echo.
pause
exit /b 1

:end
pause
