@echo off
REM Windows launcher. The implementation is in start-windows.ps1.
chcp 65001 >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-windows.ps1" %*
exit /b %ERRORLEVEL%
