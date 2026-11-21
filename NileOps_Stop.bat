@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_demo.ps1" %*
if errorlevel 1 (
    echo.
    echo [ERROR] NileOps Stop encountered an error.
    echo Press any key to close this window...
    pause >nul
    exit /b 1
)
endlocal
