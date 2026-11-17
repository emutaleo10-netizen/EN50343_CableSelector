@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" main.py
) else if exist "dist\EN50343_CableSelector.exe" (
    start "" "dist\EN50343_CableSelector.exe"
) else (
    python main.py
)
