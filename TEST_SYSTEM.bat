@echo off
echo ========================================
echo   MARAS - System Test
echo ========================================
echo.

echo [1/4] Testing Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
echo OK
echo.

echo [2/4] Testing Node.js...
node --version
if errorlevel 1 (
    echo ERROR: Node.js not found!
    pause
    exit /b 1
)
echo OK
echo.

echo [3/4] Testing Backend Dependencies...
cd backend
if not exist .venv (
    echo ERROR: Virtual environment not found! Run DEPLOY.bat first
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python -c "import fastapi, openai, playwright, supabase; print('All imports OK')"
if errorlevel 1 (
    echo ERROR: Missing dependencies! Run DEPLOY.bat first
    pause
    exit /b 1
)
echo OK
cd ..
echo.

echo [4/4] Testing Configuration...
if not exist .env (
    echo ERROR: .env file not found!
    pause
    exit /b 1
)

if not exist frontend\.env.local (
    echo ERROR: frontend\.env.local not found!
    pause
    exit /b 1
)
echo OK
echo.

echo ========================================
echo   All Tests Passed!
echo ========================================
echo.
echo System is ready to run.
echo Execute START_SERVERS.bat to start the application.
echo.
pause
