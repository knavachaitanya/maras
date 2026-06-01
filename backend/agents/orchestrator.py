import asyncio
import json
import os
import traceback
import re

from openai import AsyncOpenAI

from agents.analysis import run_analysis
from agents.qa import run_qa
from agents.research import run_research
from agents.ui_formatter import run_ui_formatter
from services.result_store import result_store
from services.supabase_client import update_session_status

AGENT_TIMEOUT_SECONDS = 60.0
PIPELINE_TIMEOUT_SECONDS = 180.0


async def orchestrate_search(query: str, job_id: str):
    """Run the agent pipeline and always publish an HTML output string."""
    print(f"[Orchestrator] ========== START ========== job_id={job_id} query={query}", flush=True)
    final_output = ""
    try:
        result_store.update_status(job_id, "running")
        try:
            await update_session_status(job_id, "running")
        except Exception as e:
            print(f"[Orchestrator] Supabase running status update skipped: {e}", flush=True)
        result_store.add_log(job_id, "Orchestrator", "start", f"Starting pipeline for query: {query}")

        try:
            final_output = await asyncio.wait_for(_run_pipeline(query, job_id), timeout=PIPELINE_TIMEOUT_SECONDS)
            print(f"[Orchestrator] Pipeline completed successfully, output length: {len(final_output)}", flush=True)
        except asyncio.TimeoutError:
            print(f"[Orchestrator] Pipeline timeout after 180 seconds", flush=True)
            result_store.add_log(job_id, "Orchestrator", "error", "Pipeline timeout after 180 seconds")
        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            print(f"[Orchestrator] {error_msg}", flush=True)
            result_store.add_log(job_id, "Orchestrator", "error", error_msg)
            result_store.add_log(job_id, "Orchestrator", "error", traceback.format_exc())

        if not final_output:
            final_output = f"<p>Results could not be completed for: <strong>{query}</strong></p>"
            print(f"[Orchestrator] No output generated, using fallback", flush=True)
    finally:
        if not final_output:
            final_output = f"<p>Results for: <strong>{query}</strong></p>"
        print(f"[Orchestrator] Setting final output: {len(final_output)} chars", flush=True)
        result_store.add_log(job_id, "Orchestrator", "complete", "Pipeline complete")
        result_store.set_output(job_id, final_output)
        result_store.update_status(job_id, "complete")
        print(f"[Orchestrator] ========== END ========== job_id={job_id}", flush=True)


async def _run_pipeline(query: str, job_id: str):
    result_store.add_log(job_id, "Orchestrator", "handoff", "Handing off to Research agent")
    intent = await analyze_query_intent(query)
    print(f"[Orchestrator] query intent: {intent.get('topic')} | keywords: {intent.get('keywords')}", flush=True)
    result_store.add_log(job_id, "Orchestrator", "info", f"Query intent: {intent.get('topic')} | keywords: {', '.join(intent.get('keywords', []))}")
    subtasks = intent.get("searchQueries") or await generate_subtasks(query)
    result_store.add_log(job_id, "Orchestrator", "info", f"Optimized search queries: {', '.join(subtasks)}")

    research_batches = []
    for subtask in subtasks:
        research_batches.append(
            asyncio.wait_for(
                run_research(job_id, subtask, subtask, result_store, intent),
                timeout=AGENT_TIMEOUT_SECONDS,
            )
        )
    settled_research = await asyncio.gather(*research_batches, return_exceptions=True)
    research_output = await asyncio.wait_for(
        asyncio.to_thread(merge_results, settled_research),
        timeout=10.0,
    )
    print(f"[Orchestrator] Research returned {len(research_output)} results", flush=True)

    result_store.add_log(job_id, "Orchestrator", "handoff", "Handing off to Analysis agent")
    analysis_output = await asyncio.wait_for(
        run_analysis(job_id, research_output, query, result_store, intent),
        timeout=AGENT_TIMEOUT_SECONDS,
    )
    print(f"[Orchestrator] Analysis returned {len(analysis_output)} results", flush=True)

    result_store.add_log(job_id, "Orchestrator", "handoff", "Handing off to QA agent")
    qa_output = await asyncio.wait_for(
        run_qa(job_id, analysis_output, query, result_store, intent),
        timeout=AGENT_TIMEOUT_SECONDS,
    )
    print(f"[Orchestrator] QA returned {len(qa_output)} results", flush=True)

    result_store.add_log(job_id, "Orchestrator", "handoff", "Handing off to UIFormatter agent")
    final_output = await asyncio.wait_for(
        run_ui_formatter(job_id, qa_output, query, result_store),
        timeout=AGENT_TIMEOUT_SECONDS,
    )
    print(f"[Orchestrator] UIFormatter returned output length: {len(final_output)}", flush=True)

    result_store.add_log(job_id, "Orchestrator", "complete", f"Pipeline complete with {len(qa_output)} results")
    return final_output


STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "up", "about", "into",
    "through", "during", "before", "after", "above", "below", "between",
    "out", "off", "over", "under", "again", "further", "then", "once", "and",
    "but", "or", "nor", "so", "yet", "both", "either", "neither", "not",
    "only", "own", "same", "than", "too", "very", "just", "what", "which",
    "who", "whom", "this", "that", "these", "those", "best", "top", "good", "how",
}


async def analyze_query_intent(query: str) -> dict:
    tokens = [
        word for word in re.sub(r"[^\w\s]", " ", query.lower()).split()
        if len(word) > 1 and word not in STOPWORDS
    ]
    intent = fallback_intent(query, tokens)

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key:
        try:
            client = AsyncOpenAI(api_key=api_key)
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    max_tokens=200,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a universal search intent analyzer. Given any user query in any language or "
                                "topic, extract the search intent. Return only valid JSON with: topic (2-4 word "
                                "summary of what they want), keywords (array of 6-8 specific meaningful words from "
                                "this exact query that relevant results must contain), category "
                                "(product/finance/technology/health/travel/food/education/news/general), priceContext "
                                "(price range mentioned or null), locationContext (location mentioned or null), "
                                "searchQueries (array of 4 specific search engine queries that will find exactly what "
                                "this user wants, each query must be about this specific topic only). Be completely "
                                "specific to the input query. Never reuse keywords from previous queries."
                            ),
                        },
                        {"role": "user", "content": f'Query: "{query}"'},
                    ],
                ),
                timeout=18.0,
            )
            parsed = json.loads(response.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip())
            if isinstance(parsed, dict):
                intent.update({key: value for key, value in parsed.items() if value is not None})
                intent["keywords"] = normalize_keywords(intent.get("keywords") or tokens, query)
                intent["searchQueries"] = normalize_search_queries(intent, query)
                return intent
        except Exception as err:
            print(f"[QueryUnderstanding] AI failed, using token fallback: {err}", flush=True)

    return intent


def fallback_intent(query: str, tokens: list[str]) -> dict:
    keywords = normalize_keywords(extract_keyphrases(query) + [token for token in tokens if len(token) > 2], query)
    topic = infer_topic(query, keywords)
    category = infer_category(query)
    price_context = infer_price_context(query)
    location_context = infer_location_context(query)
    intent = {
        "topic": topic,
        "keywords": keywords,
        "category": category,
        "priceContext": price_context,
        "locationContext": location_context,
    }
    intent["searchQueries"] = normalize_search_queries(intent, query)
    return intent


def normalize_keywords(keywords: list, query: str = "") -> list[str]:
    generic = {"best", "top", "good", "review", "reviews", "under", "below", "above"}
    output = []
    for keyword in keywords:
        word = str(keyword).lower().strip()
        if len(word) > 1 and word not in generic and word not in STOPWORDS and word not in output:
            output.append(word)
    return output[:8]


def infer_topic(query: str, keywords: list[str]) -> str:
    topic_words = [word for word in extract_query_tokens(query) if len(word) > 2]
    return " ".join(topic_words[:4]) or " ".join(keywords[:4]) or query


def infer_category(query: str) -> str:
    lower_query = query.lower()
    if re.search(r"\b(price|buy|cost|cheap|budget|under|below|deal)\b", lower_query):
        return "product"
    if re.search(r"\b(invest|fund|stock|tax|loan|finance)\b", lower_query):
        return "finance"
    if re.search(r"\b(symptom|doctor|deficiency|disease|medicine|treatment|health)\b", lower_query):
        return "health"
    if re.search(r"\b(learn|tutorial|course|beginner|study|exam)\b", lower_query):
        return "education"
    if re.search(r"\b(restaurant|dinner|lunch|food|cafe)\b", lower_query):
        return "food"
    if re.search(r"\b(news|latest|today|breaking)\b", lower_query):
        return "news"
    if re.search(r"\b(code|programming|software|computer|phone|laptop|ai)\b", lower_query):
        return "technology"
    if re.search(r"\b(hotel|flight|travel|trip|tour)\b", lower_query):
        return "travel"
    return "general"


def infer_price_context(query: str) -> str | None:
    match = re.search(r"(?:under|below|less than|upto|up to|over|above)?\s*(?:₹|rs\.?|inr|\$|€|£)?\s*(\d[\d,]*(?:\.\d+)?)\s*(?:k|m|lakh|lakhs|crore|crores)?", query.lower())
    if not match:
        return None
    amount = match.group(1).replace(",", "")
    qualifier = re.search(r"\b(under|below|less than|upto|up to|over|above)\b", query.lower())
    return f"{qualifier.group(1)} {amount}" if qualifier else amount


def infer_location_context(query: str) -> str | None:
    match = re.search(r"\b(?:in|near|around|at)\s+([a-z][a-z\s]{2,30}?)(?:\s+(?:for|with|under|below|above|near|at)\b|$)", query.lower())
    return match.group(1).strip() if match else None


def normalize_search_queries(intent: dict, query: str) -> list[str]:
    topic = intent.get("topic") or query
    keywords = intent.get("keywords") or []
    simple_keywords = [keyword for keyword in keywords if " " not in keyword]
    price_context = intent.get("priceContext") or ""
    location_context = intent.get("locationContext") or ""
    queries = [
        query,
        " ".join(simple_keywords[:6]) or " ".join(keywords[:4]),
        f"{topic} {price_context}".strip(),
        f"{topic} {location_context}".strip(),
    ]
    output = [item for item in dict.fromkeys(queries) if item]
    for suffix in ["guide", "latest", "reviews", "explained"]:
        if len(output) >= 4:
            break
        output.append(f"{topic} {suffix}".strip())
    return output[:4]


def extract_query_tokens(query: str) -> list[str]:
    return [
        word for word in re.sub(r"[^\w\s]", " ", query.lower()).split()
        if len(word) > 1 and word not in STOPWORDS
    ]


def extract_keyphrases(query: str) -> list[str]:
    words = [
        word for word in re.sub(r"[^\w\s]", " ", query.lower()).split()
        if word and word not in STOPWORDS
    ]
    phrases = []
    for first, second in zip(words, words[1:]):
        if len(first) > 2 or len(second) > 2:
            phrase = f"{first} {second}"
            if phrase not in phrases:
                phrases.append(phrase)
    return phrases[:4]


async def generate_subtasks(query: str) -> list[str]:
    try:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured")

        client = AsyncOpenAI(api_key=api_key)
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=300,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a search query optimizer. Given a user query, return a JSON array of exactly "
                            "5 specific search queries that will find the most relevant results for that exact topic. "
                            "Make each query highly specific to the user intent. Return only a valid JSON array of "
                            "strings, nothing else."
                        ),
                    },
                    {"role": "user", "content": f'User query: "{query}"'},
                ],
            ),
            timeout=20.0,
        )
        text = response.choices[0].message.content.strip()
        subtasks = json.loads(text)
        print("[Orchestrator] AI-generated subtasks:", subtasks, flush=True)
        if isinstance(subtasks, list) and subtasks:
            return [str(item).strip() for item in subtasks[:5] if str(item).strip()] or [query]
    except Exception as err:
        print(f"[Orchestrator] AI subtask generation failed, using fallback: {err}", flush=True)

    return [
        query,
        " ".join(extract_query_tokens(query)) or query,
        f"{' '.join(extract_query_tokens(query)[:4])} guide".strip(),
        f"{' '.join(extract_query_tokens(query)[:4])} latest".strip(),
    ]


def merge_results(settled_research: list) -> list:
    seen = set()
    merged = []
    for result in settled_research:
        if isinstance(result, Exception) or not isinstance(result, list):
            continue
        for item in result:
            url = (item.get("url") or "").strip()
            title = (item.get("title") or "").strip()
            if not url.startswith("http") or not title or url in seen:
                continue
            seen.add(url)
            item["url"] = url
            item["title"] = title
            merged.append(item)
    return merged
