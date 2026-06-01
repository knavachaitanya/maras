#!/usr/bin/env python3
"""Optional: Seed database with test data."""

import asyncio
import uuid
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.supabase_client import init_supabase, get_client

async def seed_test_data():
    """Create test session and results."""
    await init_supabase()
    client = get_client()
    
    session_id = str(uuid.uuid4())
    
    # Create test session
    client.table("sessions").insert({
        "id": session_id,
        "query": "test query",
        "status": "complete",
    }).execute()
    
    # Create test results
    test_results = [
        {
            "session_id": session_id,
            "rank": 1,
            "url": "https://example.com/1",
            "final_url": "https://example.com/1",
            "title": "Test Result 1",
            "description": "This is a test result",
            "content_snippet": "Test content snippet",
            "domain": "example.com",
            "favicon_url": "https://www.google.com/s2/favicons?domain=example.com&sz=32",
            "relevance_score": 0.95,
            "bm25_score": 0.9,
            "semantic_score": 0.85,
            "topic_cluster": "General",
            "is_product_page": False,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
    ]
    
    client.table("results").insert(test_results).execute()
    
    print(f" Seeded test data with session_id: {session_id}")
    print(f"   View at: http://localhost:3000/results?session={session_id}&q=test%20query")

if __name__ == "__main__":
    asyncio.run(seed_test_data())
