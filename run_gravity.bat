@echo off
echo Starting Concept 3 - Claim Gravity Model
echo Frontend: http://localhost:5179
echo Backend:  http://localhost:8006
start cmd /k "cd backend && uvicorn main:app --reload --port 8006"
start cmd /k "cd frontend && npm run dev -- --port 5179"
