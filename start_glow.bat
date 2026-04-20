@echo off
cd /d "%~dp0"
start "" .venv\Scripts\pythonw.exe glow_daemon.py
