import asyncio
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


async def run_analysis(job_id: str, research_results: list, query: str, result_store, intent: dict | None = None) -> list:
    print(f"[Analysis] received {len(research_results)} results from Research", flush=True)
    result_store.add_log(job_id, "Analysis", "start", f"Analyzing {len(research_results)} results")

    if not research_results:
        result_store.add_log(job_id, "Analysis", "error", "No raw results to analyze")
        print("[Analysis] No results received from Research agent", flush=True)
        return []

    api_key = os.environ.get("OPENAI_API_KEY", "")

    analyzed = None
    if api_key and api_key.startswith("sk-"):
        try:
            analyzed = await openai_analysis(research_results, query, api_key)
            print(f"[Analysis] OpenAI analysis complete: {len(analyzed)} results", flush=True)
            result_store.add_log(job_id, "Analysis", "info", f"OpenAI analysis complete: {len(analyzed)} results")
        except Exception as e:
            print(f"[Analysis] OpenAI analysis failed: {str(e)}, using fallback", flush=True)
            result_store.add_log(job_id, "Analysis", "error", f"OpenAI analysis failed: {str(e)}, using fallback")

    results_to_score = analyzed if isinstance(analyzed, list) else research_results
    print(f"[Analysis] Scoring {len(results_to_score)} results", flush=True)

    active_intent = intent or build_fallback_intent(query)
    scored_results = []
    for r in results_to_score:
        domain = (r.get("source_domain") or r.get("domain") or urlparse(r.get("url", "")).netloc).lower()
        r["source_domain"] = domain
        r["relevance_score"] = score_result(active_intent, r)
        r.setdefault("summary", r.get("snippet", r.get("description", ""))[:150])
        r.setdefault("category", active_intent.get("category") or r.get("category", "article"))
        r.setdefault("recommendation", "Relevant to your query")
        if r["relevance_score"] >= 20:
            scored_results.append(r)

    filtered_count = len(results_to_score) - len(scored_results)
    if filtered_count:
        result_store.add_log(job_id, "Analysis", "info", f"Filtered {filtered_count} low-relevance results below score 20")
    scored_results.sort(key=lambda item: item.get("relevance_score", 0), reverse=True)
    
    result_store.add_log(job_id, "Analysis", "complete", f"Analysis complete: {len(scored_results)} results")
    return scored_results


def score_result(intent: dict, result: dict) -> int:
    keywords = normalize_keywords(intent.get("keywords") or [])
    if not keywords:
        return min(round(float(result.get("relevance_score") or 0)), 100)
    title = (result.get("title") or "").lower()
    description = (result.get("description") or result.get("snippet") or "").lower()
    url = (result.get("url") or "").lower()
    title_description = f"{title} {description}"
    combined = f"{title_description} {url}"

    simple_keywords = [keyword for keyword in keywords if " " not in keyword]
    keyword_matches = [keyword for keyword in keywords if keyword in combined]
    visible_matches = [keyword for keyword in keywords if keyword in title_description]
    simple_visible_matches = [keyword for keyword in simple_keywords if keyword in title_description]
    required_visible = min(2, len(simple_keywords) or len(keywords))
    boundary_keywords = [keyword for keyword in simple_keywords[:1] + simple_keywords[-1:] if keyword]
    boundary_matched = not boundary_keywords or any(keyword in title_description for keyword in boundary_keywords)
    if (len(simple_visible_matches) < required_visible and len(visible_matches) < required_visible) or not boundary_matched:
        return 5
    instruction_terms = [keyword for keyword in simple_keywords if keyword in {"learn", "tutorial", "course", "beginner", "beginners", "guide"}]
    if instruction_terms and not any(keyword in title for keyword in instruction_terms):
        return 5

    score = (len(keyword_matches) / max(len(keywords), 1)) * 50

    title_matches = [keyword for keyword in keywords if keyword in title]
    score += (len(title_matches) / max(len(keywords), 1)) * 25

    price_context = intent.get("priceContext")
    if price_context:
        price_digits = "".join(ch for ch in str(price_context) if ch.isdigit())
        if price_digits and price_digits[:4] in combined:
            score += 10

    location_context = intent.get("locationContext")
    if location_context and str(location_context).lower() in combined:
        score += 10

    topic_words = [word for word in str(intent.get("topic") or "").lower().split() if len(word) > 3]
    topic_matches = [word for word in topic_words if word in combined]
    score += (len(topic_matches) / max(len(topic_words), 1)) * 5

    return min(max(round(score), 0), 100)


def normalize_keywords(keywords: list) -> list[str]:
    generic = {"best", "top", "good", "review", "reviews", "under", "below", "above"}
    output = []
    for keyword in keywords:
        word = str(keyword).lower().strip()
        if len(word) > 1 and word not in generic and word not in output:
            output.append(word)
    return output


def build_fallback_intent(query: str) -> dict:
    words = [word for word in query.lower().split() if len(word) > 2]
    category = "product" if any(word in words for word in ["price", "buy", "cost", "cheap", "budget", "under", "below"]) else "general"
    return {
        "topic": query,
        "keywords": words,
        "category": category,
        "priceContext": query if any(ch.isdigit() for ch in query) else None,
        "locationContext": None,
    }

async def openai_analysis(results: list, query: str, api_key: str) -> list:
    client = AsyncOpenAI(api_key=api_key)
    results_json = json.dumps(results[:10])
    response = await asyncio.wait_for(
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Analyze search results for relevance. "
                        "Return a JSON array with the same items. "
                        "Add these fields to every item: "
                        "relevance_score (float between 0.0 and 1.0), "
                        "summary (one sentence key insight), "
                        "category (product type or topic), "
                        "recommendation (one sentence why relevant). "
                        "Keep ALL original fields. "
                        "Return ONLY raw JSON array. "
                        "No markdown. No code fences. "
                        "Start with [ and end with ]"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Query: {query}\n\nResults: {results_json}",
                },
            ],
            temperature=0.2,
            max_tokens=2500,
        ),
        timeout=45.0,
    )
    text = response.choices[0].message.content.strip()
    if "```" in text:
        text = text[text.find("["):text.rfind("]") + 1]
    if not text.startswith("["):
        text = text[text.find("["):]
    analyzed = json.loads(text)
    return analyzed if isinstance(analyzed, list) else results
