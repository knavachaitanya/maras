@echo off
echo ========================================
echo   MARAS Database Setup
echo ========================================
echo.
echo This will check your Supabase database
echo and verify all required tables exist.
echo.
pause

cd c:\pmps
python scripts\setup_database.py

echo.
echo ========================================
echo.
echo If tables are missing, follow these steps:
echo.
echo 1. Go to: https://pxvnhzfysqmjzqbhtpgx.supabase.co
echo 2. Click "SQL Editor" in left sidebar
echo 3. Copy contents of: backend\db\schema.sql
echo 4. Paste and click "Run"
echo.
echo Then restart your backend server!
echo.
pause
