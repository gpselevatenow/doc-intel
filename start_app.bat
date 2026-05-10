@echo off
echo ===================================================
echo    Starting Elevatenow - Doc Intel Local Server
echo ===================================================

:: Start Backend
cd backend
if not exist "venv" (
    echo [INFO] First time setup: Creating Python virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo [INFO] Installing Python dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo [INFO] Starting Backend Server...
start cmd /k "title Backend API && echo DO NOT CLOSE THIS WINDOW && uvicorn main:app --host 0.0.0.0 --port 8000"

:: Start Frontend
cd ../frontend
if not exist "node_modules" (
    echo [INFO] First time setup: Installing Node dependencies...
    call npm install
)

echo [INFO] Starting Frontend UI...
start cmd /k "title Frontend UI && echo DO NOT CLOSE THIS WINDOW && npm run dev"

echo.
echo ===================================================
echo SUCCESS: The application is starting up in the background!
echo Once the terminal windows finish loading, open your browser to:
echo http://localhost:5173
echo ===================================================
pause
