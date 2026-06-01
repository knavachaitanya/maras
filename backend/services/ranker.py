from rank_bm25 import BM25Okapi
import numpy as np
from urllib.parse import urlparse
import re
from config import settings
import logging

# Try to import OpenAI, but don't fail if it's not available
try:
    import openai
    from sklearn.metrics.pairwise import cosine_similarity
    openai.api_key = settings.OPENAI_API_KEY
    OPENAI_AVAILABLE = bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"))
    if not OPENAI_AVAILABLE:
        logging.warning("OPENAI_API_KEY appears invalid")
except Exception as e:
    logging.warning(f"OpenAI not available: {e}")
    OPENAI_AVAILABLE = False

PRODUCT_URL_PATTERNS = re.compile(
    r"/(product|item|dp|p|buy|shop|listing|catalog|detail)/",
    re.IGNORECASE
)


async def get_embeddings(texts: list[str]) -> np.ndarray:
    """Get embeddings from OpenAI. Returns None if API fails."""
    if not OPENAI_AVAILABLE:
        return None
    
    try:
        resp = openai.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
            timeout=5.0
        )
        return np.array([d.embedding for d in resp.data])
    except Exception as e:
        import logging
        logging.warning(f"OpenAI API error: {e}")
        return None


async def score_results(query: str, results: list[dict]) -> list[dict]:
    """Score results using BM25 and optionally OpenAI embeddings."""
    corpus = [
        f"{r['title']} {r['description']} {r['content_snippet']}"
        for r in results
    ]

    tokenized = [doc.lower().split() for doc in corpus]

    # BM25 scoring (always works)
    bm25 = BM25Okapi(tokenized)
    bm25_scores = bm25.get_scores(query.lower().split())
    bm25_norm = bm25_scores / (bm25_scores.max() + 1e-9)

    # Try semantic scoring with OpenAI
    sem_norm = None
    try:
        all_texts = [query] + corpus
        embeddings = await get_embeddings(all_texts)
        
        if embeddings is not None:
            query_emb = embeddings[0:1]
            doc_embs = embeddings[1:]
            sem_scores = cosine_similarity(query_emb, doc_embs)[0]
            sem_norm = sem_scores / (sem_scores.max() + 1e-9)
    except Exception as e:
        import logging
        logging.warning(f"Semantic scoring failed, using BM25 only: {e}")
        sem_norm = None

    # Calculate final scores
    if sem_norm is not None:
        # Use both BM25 and semantic scores
        final_scores = (
            0.4 * bm25_norm +
            0.4 * sem_norm +
            0.2 * np.ones(len(results)) * 0.5
        )
    else:
        # Use BM25 only (fallback)
        final_scores = bm25_norm

    for i, result in enumerate(results):
        result["bm25_score"] = float(bm25_norm[i])
        result["semantic_score"] = float(sem_norm[i]) if sem_norm is not None else 0.0
        result["relevance_score"] = float(final_scores[i])

        result["is_product_page"] = bool(
            PRODUCT_URL_PATTERNS.search(result.get("url", ""))
        )

    return sorted(
        results,
        key=lambda x: x["relevance_score"],
        reverse=True
    )


def cluster_results(results: list[dict]) -> list[dict]:
    """Assign topic clusters based on domain and title keywords."""

    cluster_keywords = {
        "News": ["news", "report", "latest", "breaking", "update"],
        "Product": ["buy", "shop", "price", "amazon", "ebay", "store"],
        "Reference": ["wikipedia", "wiki", "encyclopedia", "definition"],
        "Technical": ["github", "stackoverflow", "docs", "api", "tutorial"],
        "Academic": ["research", "paper", "study", "journal", "pubmed"],
    }

    for result in results:
        text = (
            result.get("title", "") +
            " " +
            result.get("source_domain", "")
        ).lower()

        result["topic_cluster"] = "General"

        for cluster, keywords in cluster_keywords.items():
            if any(kw in text for kw in keywords):
                result["topic_cluster"] = cluster
                break

    return results


# Backward compatibility alias
rank_results = score_results
