@echo off
echo ── MARAS Setup (Windows) ──────────────────────────────────

REM 1. Copy .env
if not exist .env (
    copy .env.example .env
    echo ✔ Created .env — fill in your Supabase and OpenAI keys
)

REM 2. Python venv
cd backend
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
echo ✔ Python dependencies installed
cd ..

REM 3. Node dependencies
call npm install
cd frontend
call npm install
cd ..
echo ✔ Node dependencies installed

echo.
echo ── Supabase Schema ─────────────────────────────────────
echo Open your Supabase project → SQL Editor
echo Paste contents of backend\db\schema.sql → Run
echo Then press Enter to continue...
pause

REM 4. Generate graphify graph (optional)
call npm run graph
echo ✔ Graphify graph generated

echo.
echo ✅ Setup complete! Run: npm run dev
pause
