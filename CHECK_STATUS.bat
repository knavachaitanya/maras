@echo off
echo ========================================
echo   MARAS - Status Check
echo ========================================
echo.

echo Checking Backend (http://localhost:8000)...
curl -s http://localhost:8000/health > nul 2>&1
if errorlevel 1 (
    echo ❌ Backend is NOT running
    echo    Start with: cd backend ^&^& .venv\Scripts\activate ^&^& python start.py
) else (
    echo ✅ Backend is running
    curl -s http://localhost:8000/health
)
echo.

echo Checking Frontend (http://localhost:3000)...
curl -s http://localhost:3000 > nul 2>&1
if errorlevel 1 (
    echo ❌ Frontend is NOT running
    echo    Start with: cd frontend ^&^& npm run dev
) else (
    echo ✅ Frontend is running
)
echo.

echo ========================================
echo   Status Check Complete
echo ========================================
echo.
echo If servers are not running, execute:
echo   START_SERVERS.bat
echo.
pause
