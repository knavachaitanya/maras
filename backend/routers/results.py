from fastapi import APIRouter, HTTPException
from services.result_store import result_store
from services.supabase_client import get_client

router = APIRouter()

@router.get("/results/{job_id}")
async def get_results(job_id: str):
    memory_result = result_store.get_result(job_id)
    client = get_client()
    if client:
        try:
            session_res = client.table("sessions").select("*").eq("id", job_id).execute()
            results_res = client.table("results").select("*").eq("session_id", job_id).order("rank").execute()
            if session_res.data:
                session = session_res.data[0]
                if memory_result and memory_result.get("status") == "complete":
                    session["status"] = "complete"
                    rows = sorted(memory_result.get("results") or [], key=lambda item: item.get("rank", 0))
                else:
                    rows = results_res.data or sorted((memory_result or {}).get("results") or [], key=lambda item: item.get("rank", 0))
                return {
                    "session": session,
                    "results": rows,
                    "job_id": job_id,
                    "status": session.get("status", "pending"),
                    "query": session.get("query", ""),
                    "output": (memory_result or {}).get("output", ""),
                    "error": (memory_result or {}).get("error", ""),
                }
        except Exception as e:
            print(f"[ResultsRouter] Supabase fetch failed, using memory store: {e}", flush=True)
    
    result = memory_result
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")

    session = {
        "id": job_id,
        "status": result["status"],
        "query": result["query"],
        "created_at": result["created_at"],
        "updated_at": result["updated_at"],
        "error": result.get("error") or "",
    }
    rows = sorted(result.get("results") or [], key=lambda item: item.get("rank", 0))
    return {
        "session": session,
        "results": rows,
        "job_id": job_id,
        "status": result["status"],
        "query": result["query"],
        "output": result.get("output") or "",
        "error": result.get("error") or "",
        "created_at": result["created_at"],
        "updated_at": result["updated_at"]
    }

@router.get("/results/{job_id}/logs")
async def get_logs(job_id: str):
    result = result_store.get_result(job_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "status": result.get("status") or "pending",
        "logs": result.get("logs") or [],
        "output": result.get("output") or "",
        "error": result.get("error") or ""
    }

