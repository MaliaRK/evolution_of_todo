@echo off
REM Batch script to run the Todo AI System locally for testing

echo Starting Todo AI System...

REM Start the backend in a separate window
echo Starting backend server...
start cmd /k "cd backend && python -m uvicorn src.main:app --reload --port 8000"

REM Give the backend a moment to start
timeout /t 5 /nobreak

REM Start the frontend in a separate window
echo Starting frontend server...
start cmd /k "cd frontend && npm run dev"

echo Both backend and frontend should now be starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit...
pause >nul