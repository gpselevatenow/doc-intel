@echo off
echo Starting Option 3 - Streaming Shell
echo Frontend: http://localhost:5175
echo Backend:  http://localhost:8002
start cmd /k "cd backend && uvicorn main:app --reload --port 8002"
start cmd /k "cd frontend && npm run dev -- --port 5175"
