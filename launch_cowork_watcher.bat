@echo off
cd /d "%~dp0"
start "" .venv\Scripts\pythonw.exe glow_cowork_watcher.py
echo [orange-glow] cowork notification watcher started. You can close this window.
timeout /t 2 >nul
