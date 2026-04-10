@echo off
setlocal
cd /d "%~dp0"
start "Talk2Shell" cmd /k python main.py --launcher
