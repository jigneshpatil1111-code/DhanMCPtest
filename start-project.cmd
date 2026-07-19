@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-project.ps1"
exit /b %ERRORLEVEL%
