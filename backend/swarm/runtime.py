from agents.orchestrator import orchestrate_search
from services.result_store import result_store


async def run_agent_pipeline(session_id: str, query: str):
    """Backward-compatible wrapper around the current orchestrator."""
    result_store.create_job(session_id, query)
    await orchestrate_search(query, session_id)
    result = result_store.get_result(session_id) or {}
    return result.get("output") or ""
