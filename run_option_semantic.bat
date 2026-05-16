@echo off
echo Starting Semantic Lens
echo Frontend: http://localhost:5176
echo Backend:  http://localhost:8003
start cmd /k "cd backend && uvicorn main:app --reload --port 8003"
start cmd /k "cd frontend && npm run dev -- --port 5176"
