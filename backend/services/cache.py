# backend/services/cache.py
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional

# In-memory cache for ultra-fast responses
_memory_cache = {}

def get_cache_key(query: str) -> str:
    """Generate cache key from query."""
    return hashlib.md5(query.lower().strip().encode()).hexdigest()

def get_cached_results(query: str) -> Optional[dict]:
    """Get cached results if available and not expired."""
    key = get_cache_key(query)
    if key in _memory_cache:
        cached = _memory_cache[key]
        # Check if expired (5 minutes for fast mode)
        if datetime.fromisoformat(cached["cached_at"]) > datetime.utcnow() - timedelta(minutes=5):
            return cached["results"]
        else:
            # Expired, remove from cache
            del _memory_cache[key]
    return None

def set_cached_results(query: str, results: dict):
    """Cache results in memory."""
    key = get_cache_key(query)
    _memory_cache[key] = {
        "results": results,
        "cached_at": datetime.utcnow().isoformat()
    }
    
    # Limit cache size to 100 entries
    if len(_memory_cache) > 100:
        # Remove oldest entry
        oldest_key = min(_memory_cache.keys(), 
                        key=lambda k: _memory_cache[k]["cached_at"])
        del _memory_cache[oldest_key]

def clear_cache():
    """Clear all cached results."""
    _memory_cache.clear()
