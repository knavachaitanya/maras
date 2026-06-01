# backend/swarm/protocols.py
from pydantic import BaseModel
from typing import Optional, List, Any

class AgentMessage(BaseModel):
    session_id: str
    from_agent: str
    to_agent: str
    payload_key: str          # key in context_variables being handed off
    status: str               # "ok" | "warn" | "error"
    message: Optional[str] = None

class RawResult(BaseModel):
    url: str
    title: str
    description: str
    content_snippet: str
    source_domain: str
    scraped_at: str
    og_image: Optional[str] = None

class ScoredResult(RawResult):
    relevance_score: float
    rank: int
    bm25_score: float
    semantic_score: float
    topic_cluster: str
    is_product_page: bool

class ValidatedResult(ScoredResult):
    final_url: str

class SearchResponse(BaseModel):
    session_id: str
    query: str
    total: int
    results: List[dict]
    clusters: dict
    generated_at: str
