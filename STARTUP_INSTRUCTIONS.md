# Quick Startup Instructions

## ⚠️ Important: You need to start BOTH servers!

### Step 1: Setup Database (One-time only)

1. Go to your Supabase project: https://pxvnhzfysqmjzqbhtpgx.supabase.co
2. Click **SQL Editor** in the left sidebar
3. Open the file `backend/db/schema.sql` in a text editor
4. Copy ALL the contents
5. Paste into Supabase SQL Editor
6. Click **Run** (or press Ctrl+Enter)
7. You should see "Success. No rows returned"

### Step 2: Start Backend Server

Open a terminal and run:

```bash
cd backend
.venv\Scripts\activate
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!**

### Step 3: Start Frontend Server

Open a **NEW** terminal and run:

```bash
cd frontend
npm run dev
```

You should see:
```
Local: http://localhost:3000
```

**Keep this terminal open too!**

### Step 4: Test

1. Open browser to http://localhost:3000
2. Enter a search query
3. Wait for results (may take 10-30 seconds for first query)

## Troubleshooting

### Backend won't start?

Check if dependencies are installed:
```bash
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### Frontend won't start?

Check if dependencies are installed:
```bash
cd frontend
npm install
```

### Still no results?

1. Check backend terminal for errors
2. Check browser console (F12 → Console)
3. Verify database tables exist in Supabase
4. Make sure both servers are running

## Quick Check

Backend running? → http://localhost:8000/health should show `{"status":"ok"}`
Frontend running? → http://localhost:3000 should show the search page
