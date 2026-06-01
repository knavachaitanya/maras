import sys
import io

# Force UTF-8 encoding for stdout and stderr on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from routers import search, results, graph, ws
from services.supabase_client import init_supabase
import uvicorn
import asyncio
import os
from pathlib import Path
from time import time
from collections import defaultdict

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Fix for Windows asyncio subprocess issues
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Simple in-memory rate limiter
rate_limit_store = defaultdict(list)

def check_rate_limit(ip: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
    """Check if IP has exceeded rate limit. Returns True if allowed."""
    now = time()
    cutoff = now - window_seconds
    
    # Remove old entries
    rate_limit_store[ip] = [t for t in rate_limit_store[ip] if t > cutoff]
    
    # Check limit
    if len(rate_limit_store[ip]) >= max_requests:
        return False
    
    # Add current request
    rate_limit_store[ip].append(now)
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("="*60, flush=True)
    print("MARAS Backend Starting", flush=True)
    print("="*60, flush=True)
    print("Backend starting on port", os.environ.get("PORT", "8000"), flush=True)
    print("CORS allowed origins:", allowed_origins, flush=True)
    print("OpenAI key:", "configured" if os.environ.get('OPENAI_API_KEY', '').startswith('sk-') else "not configured", flush=True)
    for agent_name in ["Orchestrator", "Research", "Analysis", "QA", "UIFormatter"]:
        print(f"{agent_name} agent initialized and listening", flush=True)
    print("="*60, flush=True)
    try:
        await init_supabase()
    except Exception as e:
        print(f"Supabase initialization skipped: {e}", flush=True)
    yield
    print("Backend shutting down", flush=True)

app = FastAPI(
    title="MARAS API",
    description="MultiAgent Research and Aggregation System",
    version="1.0.0",
    lifespan=lifespan,
)

# Read allowed origins from environment variable
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limit POST /api/search to 10 requests per minute per IP."""
    if request.method == "POST" and request.url.path == "/api/search":
        client_ip = request.client.host if request.client else "unknown"
        
        if not check_rate_limit(client_ip):
            raise HTTPException(status_code=429, detail="Too many requests, please wait")
    
    response = await call_next(request)
    return response

app.include_router(search.router,  prefix="/api")
app.include_router(results.router, prefix="/api")
app.include_router(graph.router,   prefix="/api")
app.include_router(ws.router)

@app.get("/health")
async def health(): 
    return {
        "status": "ok",
        "agents": ["Orchestrator", "Research", "Analysis", "QA", "UIFormatter"],
        "version": "1.0.0"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Backend running on port {port}")
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        reload_dirs=["./"],
        reload_includes=["*.py"],
        reload_excludes=["*/.venv/*", "*/__pycache__/*", "*.pyc", ".venv/*"]
    )
