@echo off
echo Starting Concept 1 - Extraction Heartbeat
echo Frontend: http://localhost:5177
echo Backend:  http://localhost:8004
start cmd /k "cd backend && uvicorn main:app --reload --port 8004"
start cmd /k "cd frontend && npm run dev -- --port 5177"
