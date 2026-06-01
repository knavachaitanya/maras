@echo off
echo ========================================
echo   MARAS - Deployment Setup
echo ========================================
echo.

echo [1/5] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.11+
    pause
    exit /b 1
)
echo.

echo [2/5] Setting up Backend...
cd backend

echo Installing Playwright browsers (one-time setup)...
python -m playwright install chromium
if errorlevel 1 (
    echo WARNING: Playwright install failed, will try to continue...
)
echo.

echo Installing Python dependencies...
if exist .venv (
    echo Virtual environment exists, activating...
    call .venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)
echo.

cd ..

echo [3/5] Setting up Frontend...
cd frontend

if not exist node_modules (
    echo Installing Node dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install Node dependencies
        pause
        exit /b 1
    )
) else (
    echo Node modules already installed
)
echo.

cd ..

echo [4/5] Verifying Configuration...
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create .env file with your API keys
    pause
    exit /b 1
)

if not exist frontend\.env.local (
    echo ERROR: frontend\.env.local not found!
    echo Please create frontend\.env.local file
    pause
    exit /b 1
)

echo Configuration files found!
echo.

echo [5/5] Setup Complete!
echo.
echo ========================================
echo   Ready to Deploy!
echo ========================================
echo.
echo To start the servers, run:
echo   START_SERVERS.bat
echo.
echo Or start manually:
echo   Backend:  cd backend ^&^& .venv\Scripts\activate ^&^& python start.py
echo   Frontend: cd frontend ^&^& npm run dev
echo.
pause
