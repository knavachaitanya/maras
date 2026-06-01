#!/usr/bin/env python3
"""
Simple startup script for MARAS backend.
This bypasses complex dependencies and starts the server quickly.
"""
import sys
import io
import os
import asyncio

# Force UTF-8 encoding for stdout and stderr on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Fix for Windows asyncio subprocess issues
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    import uvicorn
    print("Starting MARAS Backend (Fast Mode)")
    print("Server: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Fast Mode: Enabled")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
