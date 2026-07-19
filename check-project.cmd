@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0check-project.ps1"
exit /b %ERRORLEVEL%
