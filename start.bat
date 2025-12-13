@echo off
cd /d %~dp0
if not exist venv (
    python -m venv venv
    powershell venv\Scripts\activate.ps1
    pip install -r requirements.txt
    python -m pip install --upgrade pip
    python main.py
) else (
    powershell venv\Scripts\activate.ps1
    python main.py
)