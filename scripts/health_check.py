#!/usr/bin/env python3
"""Health check script to validate all services are running."""

import httpx
import sys
import asyncio

async def check_backend():
    """Check if backend is responding."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code == 200:
                print(" Backend: OK")
                return True
            else:
                print(f" Backend: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f" Backend: {e}")
        return False

async def check_frontend():
    """Check if frontend is responding."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:3000", timeout=5.0)
            if response.status_code == 200:
                print(" Frontend: OK")
                return True
            else:
                print(f" Frontend: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f" Frontend: {e}")
        return False

async def main():
    print(" Checking MARAS services...\n")
    
    backend_ok = await check_backend()
    frontend_ok = await check_frontend()
    
    print()
    if backend_ok and frontend_ok:
        print(" All services are healthy!")
        sys.exit(0)
    else:
        print(" Some services are down. Check logs.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
