@echo off
cd /d "%~dp0"
if not exist venv_nuevo (
    py -m venv venv_nuevo
)
call venv_nuevo\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
pause
