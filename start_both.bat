@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo Creating virtual environment with Python 3.13...
    py -3.13 -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
start "Backend" cmd /k "python -m uvicorn main:app --host 127.0.0.1 --port 8002"
start "Frontend" cmd /k "python -m streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 127.0.0.1"
echo Backend running at http://127.0.0.1:8002/docs
echo Frontend running at http://127.0.0.1:8501
pause
