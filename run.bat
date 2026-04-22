@echo off
cd /d "%~dp0"
start "" "%~dp0.venv\Scripts\streamlit.exe" run "%~dp0app.py"
