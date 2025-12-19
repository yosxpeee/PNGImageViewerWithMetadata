@echo off
cd /d %~dp0
if not exist venv (
    python -m venv venv
    venv\Scripts\activate.bat
    pip install -r requirements.txt
    python -m pip install --upgrade pip
    flet run main.py
) else (
    venv\Scripts\activate.bat
    flet run main.py
)