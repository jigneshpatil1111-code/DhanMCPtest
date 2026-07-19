@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-project.ps1"
exit /b %ERRORLEVEL%
