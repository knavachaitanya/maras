from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from agents.orchestrator import orchestrate_search
from services.result_store import result_store
from services.supabase_client import create_session
import uuid

router = APIRouter()


class SearchRequest(BaseModel):
    query: str


@router.post("/search")
async def search(req: SearchRequest, bg: BackgroundTasks):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    job_id = str(uuid.uuid4())
    
    print(f"[SearchRouter] Creating job {job_id} for query: {query}", flush=True)
    result_store.create_job(job_id, query)
    try:
        await create_session(job_id, query)
    except Exception as e:
        print(f"[SearchRouter] Supabase session create skipped: {e}", flush=True)
    
    print(f"[SearchRouter] Adding background task for job {job_id}", flush=True)
    bg.add_task(orchestrate_search, query, job_id)
    
    print(f"[SearchRouter] Returning job_id {job_id}", flush=True)
    return {
        "job_id": job_id,
        "status": "started"
    }
