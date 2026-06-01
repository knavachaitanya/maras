@echo off
echo ========================================
echo   MARAS - Starting Servers
echo ========================================
echo.
echo Starting Backend and Frontend...
echo.
echo Backend will run on: http://localhost:8000
echo Frontend will run on: http://localhost:3000
echo.
echo Press Ctrl+C to stop all servers
echo.

REM Start backend in a new window
start "MARAS Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\activate && python start.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend in a new window
start "MARAS Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   Servers Starting...
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Wait 10-15 seconds for servers to fully start
echo Then open: http://localhost:3000
echo.
echo Close the server windows to stop the application
echo.
pause
