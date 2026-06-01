from supabase import create_client, Client
from config import settings
import hashlib, json
from datetime import datetime, timedelta, timezone

_client: Client = None

supabase = None  # Global instance
RESULT_COLUMNS = {
    "session_id", "title", "url", "description", "snippet", "source_domain",
    "relevance_score", "rank", "category", "is_verified", "og_image", "price"
}

async def init_supabase():
    global _client, supabase
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        _client = None
        supabase = None
        return
    _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    supabase = _client
    await check_results_schema()

def get_client() -> Client:
    return _client

async def check_results_schema():
    if not _client:
        return
    try:
        _client.table("results").select(",".join(sorted(RESULT_COLUMNS))).limit(1).execute()
        print("Supabase results schema: required formatter columns available", flush=True)
    except Exception as e:
        print(
            "Supabase results schema missing one or more formatter columns. "
            "Add these columns in Supabase dashboard if inserts fail: "
            "session_id, title, url, description, snippet, source_domain, "
            "relevance_score, rank, category, is_verified, og_image, price. "
            f"Schema check error: {e}",
            flush=True,
        )

async def create_session(session_id: str, query: str):
    if _client:
        _client.table("sessions").upsert({
            "id": session_id,
            "query": query,
            "status": "pending",
        }).execute()

async def log_agent_event(agent: str, event: str, message: str, ctx: dict):
    if _client:
        _client.table("agent_logs").insert({
            "session_id": ctx.get("session_id"),
            "agent_name": agent,
            "event_type": event,
            "message": message,
            "metadata": {"query": ctx.get("query")},
        }).execute()

async def update_session_status(session_id: str, status: str, results=None):
    if _client:
        # Update session status
        _client.table("sessions").update({
            "status": status
        }).eq("id", session_id).execute()
        
        if results is not None:
            await save_results(session_id, {"results": results})

async def save_results(session_id: str, payload: dict):
    if _client:
        rows = []
        for idx, result in enumerate(payload["results"]):
            rows.append({
                "session_id": session_id,
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "description": result.get("description", ""),
                "snippet": result.get("snippet") or result.get("description", ""),
                "source_domain": result.get("source_domain") or result.get("domain", ""),
                "domain": result.get("domain") or result.get("source_domain", ""),
                "favicon_url": result.get("favicon_url", ""),
                "og_image": result.get("og_image", ""),
                "price": result.get("price", ""),
                "relevance_score": result.get("relevance_score", 0),
                "rank": result.get("rank", idx + 1),
                "category": result.get("category", "article"),
                "is_product_page": result.get("is_product_page", False),
                "is_verified": result.get("is_verified", True),
            })
        if rows:
            _client.table("results").delete().eq("session_id", session_id).execute()
            _client.table("results").insert(rows).execute()

async def cache_scrape(query: str, results: list, ttl_minutes: int = 30):
    if _client:
        h = hashlib.md5(query.encode()).hexdigest()
        expires = (datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).isoformat()
        _client.table("scrape_cache").upsert({
            "query_hash": h, "query": query,
            "results": json.dumps(results), "expires_at": expires,
        }).execute()

async def get_cached_scrape(query: str) -> list | None:
    if not _client:
        return None
    h = hashlib.md5(query.encode()).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    res = (_client.table("scrape_cache")
           .select("results")
           .eq("query_hash", h)
           .gt("expires_at", now)
           .execute())
    if res.data:
        return json.loads(res.data[0]["results"])
    return None

