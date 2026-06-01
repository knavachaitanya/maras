# Fix Instructions - "Something went wrong" Error

## The Issue
The application shows "Something went wrong. Please try again." when searching. This is caused by:

1. **Windows AsyncIO Issue** - Playwright (browser automation) doesn't work with Windows' default event loop
2. **Backend needs restart** - The fix has been applied but requires a restart

## The Solution (3 Steps)

### Step 1: Stop All Servers

**In the terminal running the BACKEND:**
- Press `Ctrl+C` to stop it

**In the terminal running the FRONTEND:**
- Press `Ctrl+C` to stop it

### Step 2: Restart Backend with Fix

Open a **new terminal** and run:

```bash
cd c:\pmps\backend
python start.py
```

**Wait for this message:**
```
🚀 Starting MARAS Backend (Fast Mode)
📍 Server: http://localhost:8000
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Restart Frontend

Open **another new terminal** and run:

```bash
cd c:\pmps\frontend
npm run dev
```

**Wait for this message:**
```
✓ Ready in 5s
Local: http://localhost:3000
```

### Step 4: Test

1. Open http://localhost:3000 in your browser
2. Search for "laptops under 74000 rupees"
3. You should see results in 2-3 seconds!

---

## What Was Fixed

I added this code to `backend/main.py` and `backend/start.py`:

```python
import asyncio
import sys

# Fix for Windows asyncio subprocess issues
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

This tells Python to use the correct event loop on Windows that supports subprocess operations (needed for Playwright browser automation).

---

## Verification

### Check Backend is Running
Open in browser: http://localhost:8000/health

Should show:
```json
{"status": "ok"}
```

### Check Frontend is Running
Open in browser: http://localhost:3000

Should show the search interface.

### Run Test Script
```bash
cd c:\pmps
python test_search.py
```

Should show:
```
✅ Health check: {'status': 'ok'}
✅ Search initiated: ...
✅ Final status: complete
✅ All tests passed!
```

---

## Still Not Working?

### Option 1: Use the Batch Scripts

**Check Status:**
```bash
CHECK_STATUS.bat
```

**Restart Backend:**
```bash
RESTART_BACKEND.bat
```

### Option 2: Check for Errors

**Look at the backend terminal** for error messages. Common errors:

1. **"Address already in use"** - Port 8000 is taken
   ```bash
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

2. **"Module not found"** - Missing dependencies
   ```bash
   cd backend
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **"Connection refused"** - Backend not running
   ```bash
   cd backend
   python start.py
   ```

### Option 3: Fresh Start

1. **Stop everything** (Ctrl+C in all terminals)
2. **Close all terminals**
3. **Open a new terminal** and run:
   ```bash
   cd c:\pmps
   START_SERVERS.bat
   ```

---

## Technical Details

### Why This Happens on Windows

- **Playwright** launches a Chromium browser as a subprocess
- Windows has two asyncio event loops:
  - `ProactorEventLoop` (default) - No subprocess support ❌
  - `SelectorEventLoop` - Supports subprocesses ✅
- The fix switches to `SelectorEventLoop` on Windows

### Files Modified

- ✅ `backend/main.py` - Added Windows event loop fix
- ✅ `backend/start.py` - Added Windows event loop fix
- ✅ `test_search.py` - Created test script
- ✅ `CHECK_STATUS.bat` - Created status checker
- ✅ `RESTART_BACKEND.bat` - Created restart script

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `CHECK_STATUS.bat` | Check if servers are running |
| `RESTART_BACKEND.bat` | Restart backend server |
| `python test_search.py` | Test search functionality |
| `START_SERVERS.bat` | Start both servers |

---

## Need More Help?

1. Read `TROUBLESHOOTING.md` for common issues
2. Read `WINDOWS_FIX.md` for technical details
3. Check backend terminal for error messages
4. Run `python test_search.py` to diagnose issues

---

## Expected Behavior After Fix

✅ Backend starts without errors  
✅ Frontend connects successfully  
✅ Search returns results in 2-3 seconds  
✅ No "Something went wrong" error  
✅ Agent status indicators work  
✅ Results display properly  

**The fix is applied - just restart the servers!** 🚀
