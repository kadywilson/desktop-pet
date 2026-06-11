@echo off
REM Daily launch script - shows brief startup info then starts silently
REM 日常启动脚本 - 显示简要启动信息，然后静默运行
REM
REM For debugging: use run_pet_debug.bat instead
REM 调试：请改用 run_pet_debug.bat

echo.
echo ========================================
echo Desktop Pet - Starting up...
echo 桌宠 - 正在启动...
echo.
echo Tips:
echo - Click on pet / 点击桌宠: AI chat
echo - Double click on pet / 双击桌宠: AI conversation
echo - Tray menu / 托盘菜单: Show/Hide/Todo/Logs/Quit
echo - Logs saved to / 日志保存至: logs/pet_app.log
echo.
echo For debugging output, use run_pet_debug.bat
echo 如需调试输出，请使用 run_pet_debug.bat
echo ========================================
echo.

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
start "" python -m pet_app.main
timeout /t 2 /nobreak
exit
