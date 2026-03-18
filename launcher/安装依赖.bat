@echo off
REM 安装 Claude Code 启动器所需的 Python 依赖

cd /d "%~dp0"

echo ========================================
echo    Claude Code 启动器 - 依赖安装
echo ========================================
echo.
echo 正在安装依赖...
echo - pywin32: 用于修改窗口标题
echo - psutil: 用于进程检测
echo.

python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ❌ 安装失败
    echo.
    echo 请确保：
    echo 1. 已安装 Python 3.8+
    echo 2. pip 已正确配置
    echo 3. 有网络连接
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✓ 依赖安装完成！
echo ========================================
echo.
echo 说明：
echo - 如果没有 pywin32，窗口标题功能将被跳过
echo - 其他功能不受影响
echo.
pause
