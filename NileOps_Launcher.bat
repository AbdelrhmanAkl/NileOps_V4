@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\launch_demo.ps1" %*
if errorlevel 1 (
    echo.
    echo [ERROR] NileOps Launcher encountered an error.
    echo Press any key to close this window...
    pause >nul
    exit /b 1
)
endlocal
