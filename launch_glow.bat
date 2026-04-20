@echo off
cd /d "%~dp0"
start "" .venv\Scripts\pythonw.exe glow_daemon.py
echo [orange-glow] started. You can close this window.
timeout /t 2 >nul
