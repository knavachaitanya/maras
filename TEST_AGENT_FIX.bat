@echo off
echo ================================================================================
echo TESTING AGENT PIPELINE FIX
echo ================================================================================
echo.
echo This script will test if the agent pipeline is working correctly.
echo.
echo Prerequisites:
echo   1. Backend must be running on http://localhost:8000
echo   2. Supabase database must be accessible
echo   3. OpenAI API key must be set in .env
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Running test script...
echo.

cd /d "%~dp0"
python test_agent_pipeline.py

echo.
echo ================================================================================
echo TEST COMPLETE
echo ================================================================================
echo.
echo If all tests passed, the agent pipeline is working correctly!
echo.
echo Next steps:
echo   1. Start the frontend: cd frontend ^&^& npm run dev
echo   2. Open http://localhost:3000 in your browser
echo   3. Submit a search query
echo   4. Watch the agent status dots change from grey to blue to green
echo.
pause
