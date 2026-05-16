@echo off
echo Starting Option 2 - Claim Delta View
echo Frontend: http://localhost:5174
echo Backend:  http://localhost:8001
start cmd /k "cd backend && uvicorn main:app --reload --port 8001"
start cmd /k "cd frontend && npm run dev -- --port 5174"
