@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo Creating virtual environment...
    py -3.12 -m venv .venv
)
call .venv\Scripts\activate
python -m pip install -r requirements.txt
python ingestion/ingest.py
start "FastAPI" .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001
start "Streamlit" .venv\Scripts\python.exe -m streamlit run frontend/streamlit_app.py
echo.
echo Backend: http://127.0.0.1:8001/docs
echo Frontend: http://127.0.0.1:8501
echo.
echo Test commands:
echo   curl http://127.0.0.1:8001/health
echo   curl -X POST http://127.0.0.1:8001/chat -H "Content-Type: application/json" -d "{\"message\":\"Explain this code: def add(a,b): return a+b\"}"
echo   pytest -q
pause
