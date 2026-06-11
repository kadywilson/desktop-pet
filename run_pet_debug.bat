@echo off
REM Debug launch script - shows console with live logs
REM 调试启动脚本 - 显示控制台和实时日志

cd /d %~dp0
where conda >nul 2>nul
if errorlevel 1 (
    echo Conda was not found on PATH. Please open an Anaconda Prompt or add conda to PATH.
    pause
    exit /b 1
)

call conda activate desktop-pet
if errorlevel 1 (
    echo Failed to activate conda environment: desktop-pet
    pause
    exit /b 1
)

set PYTHONPATH=src
python -m pet_app.main
pause
