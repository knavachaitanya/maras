# Windows AsyncIO Fix

## Problem
The application was showing "Something went wrong. Please try again." error when searching. The backend logs showed:

```
NotImplementedError
File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64__qbz5n2kfra8p0\Lib\asyncio\base_events.py", line 1708, in subprocess_exec
    transport, protocol = await loop.subprocess_exec(
```

## Root Cause
The scraper service uses **Playwright** to launch a browser subprocess for web scraping. On Windows, the default asyncio event loop (`ProactorEventLoop`) doesn't support subprocess operations properly, causing a `NotImplementedError`.

## Solution
Set the Windows-specific event loop policy to `WindowsSelectorEventLoopPolicy` which supports subprocess operations:

```python
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

This fix has been applied to:
- `backend/main.py` - Main FastAPI application
- `backend/start.py` - Startup script

## How to Test
1. **Restart the backend server** (if it's currently running):
   - Press `Ctrl+C` in the terminal running the backend
   - Start it again with: `cd backend && python start.py`

2. **Try a search** in the frontend:
   - Go to http://localhost:3000
   - Search for "laptops under 74000 rupees" or any other query
   - You should now see results instead of an error

## Technical Details
- **Playwright** requires subprocess support to launch Chromium browser
- Windows has two event loop implementations:
  - `ProactorEventLoop` (default) - Better for I/O but no subprocess support
  - `SelectorEventLoop` - Supports subprocesses but slightly slower for I/O
- The fix switches to `SelectorEventLoop` on Windows only
- Other platforms (Linux, macOS) are unaffected

## Related Files
- `backend/services/scraper.py` - Uses Playwright for web scraping
- `backend/agents/research.py` - Calls the scraper service
- `backend/swarm/runtime.py` - Orchestrates the agent pipeline
