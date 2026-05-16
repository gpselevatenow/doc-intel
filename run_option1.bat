@echo off
echo Starting Option 1 - Ambient Risk Score
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
start cmd /k "cd backend && uvicorn main:app --reload --port 8000"
start cmd /k "cd frontend && npm run dev -- --port 5173"
