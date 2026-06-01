@echo off
echo ========================================
echo   RESTARTING MARAS BACKEND
echo ========================================
echo.
echo Stopping any running backend processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *start.py*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting backend server...
cd backend
python start.py
