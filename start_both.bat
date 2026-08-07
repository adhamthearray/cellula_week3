@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\activate
start "Backend" cmd /k "python -m uvicorn main:app --host 127.0.0.1 --port 8002"
start "Frontend" cmd /k "python -m streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 127.0.0.1"
echo Backend running at http://127.0.0.1:8002/docs
echo Frontend running at http://127.0.0.1:8501
pause
