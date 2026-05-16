@echo off
echo Starting Concept 6 - Predictive Ghost Fields
echo Frontend: http://localhost:5178
echo Backend:  http://localhost:8005
start cmd /k "cd backend && uvicorn main:app --reload --port 8005"
start cmd /k "cd frontend && npm run dev -- --port 5178"
