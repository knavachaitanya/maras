# Simple Start Guide

## The Issue

You're seeing "Searching..." because the **backend server is not running**.

## Solution: Start Both Servers

### Terminal 1: Backend

```bash
cd C:\Users\chait\OneDrive\Desktop\newai\backend
.venv\Scripts\activate
python main.py
```

Wait until you see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!**

### Terminal 2: Frontend

Open a NEW terminal:

```bash
cd C:\Users\chait\OneDrive\Desktop\newai\frontend
npm run dev
```

Wait until you see:
```
Local: http://localhost:3000
```

**Keep this terminal open too!**

### Test

1. Open browser: http://localhost:3000
2. Enter search query
3. Wait for results (10-30 seconds)

## If Backend Won't Start

The dependencies are still installing. Wait a few minutes, then try again.

Or install manually:

```bash
cd C:\Users\chait\OneDrive\Desktop\newai\backend
.venv\Scripts\activate
pip install fastapi uvicorn openai-swarm playwright beautifulsoup4 httpx rank-bm25 openai scikit-learn numpy supabase pydantic pydantic-settings python-dotenv anyio
playwright install chromium
```

## Database Setup (One-Time)

1. Go to: https://pxvnhzfysqmjzqbhtpgx.supabase.co
2. Click "SQL Editor"
3. Copy ALL of `backend/db/schema.sql`
4. Paste and Run

## Quick Check

- Backend health: http://localhost:8000/health
- Should show: `{"status":"ok"}`

## Common Issues

**"Module not found"** → Dependencies still installing, wait
**"Connection refused"** → Backend not running, start it
**"No results"** → Check both terminals for errors
