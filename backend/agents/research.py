import asyncio
import json
import os
import re
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
REDDIT_HEADERS = {"User-Agent": "Mozilla/5.0 MARAS-Bot/1.0"}
DDG_HEADERS = {"User-Agent": "MARAS-Bot/1.0", "Accept": "application/json"}


def _log(result_store, job_id: str, message: str, event: str = "info") -> None:
    print(f"[ResearchAgent] {message}", flush=True)
    if result_store:
        result_store.add_log(job_id, "Research", event, message)


async def run_research(job_id: str, input_data: str, query: str, result_store, intent: dict | None = None) -> list:
    query = query or input_data
    _log(result_store, job_id, f"research:start query={query}")

    results = await multi_source_search(query, job_id, result_store, intent)
    print(f"[Research] raw results count: {len(results)}", flush=True)
    _log(result_store, job_id, f"final merged array length before analysis:start = {len(results)}")

    if not results:
        _log(result_store, job_id, "ALL SOURCES FAILED: emitting analysis:start with empty array", "error")
        return []

    _log(result_store, job_id, f"research:complete real_results={len(results)}", "complete")
    return results


async def multi_source_search(query: str, job_id: str = "", result_store=None, intent: dict | None = None) -> list[dict]:
    search_queries = (intent or {}).get("searchQueries") or [query]
    wikipedia_query = search_queries[0] if len(search_queries) > 0 else query
    reddit_query = search_queries[1] if len(search_queries) > 1 else wikipedia_query
    hn_query = search_queries[2] if len(search_queries) > 2 else wikipedia_query
    ddg_query = search_queries[3] if len(search_queries) > 3 else wikipedia_query
    search_query = query
    sources = [
        ("Wikipedia", wikipedia_search(wikipedia_query, job_id, result_store)),
        ("Reddit", reddit_search(reddit_query, job_id, result_store)),
        ("HackerNews", hackernews_search(hn_query, job_id, result_store)),
        ("DuckDuckGoInstant", duckduckgo_instant_search(ddg_query, job_id, result_store)),
        ("BingHTML", bing_html_search(search_query, job_id, result_store)),
    ]
    if os.environ.get("OPENAI_API_KEY"):
        sources.append(("OpenAI", openai_search_suggestions(query, job_id, result_store)))
    if os.environ.get("SERPAPI_KEY"):
        sources.append(("SerpAPI", serpapi_search(query, job_id, result_store)))
    if os.environ.get("BRAVE_API_KEY"):
        sources.append(("Brave", brave_search(query, job_id, result_store)))
    if os.environ.get("GOOGLE_API_KEY"):
        sources.append(("Google", google_search(query, job_id, result_store)))
    if os.environ.get("BING_API_KEY"):
        sources.append(("Bing", bing_search(query, job_id, result_store)))

    _log(result_store, job_id, "starting all source fetches in parallel")
    settled = await asyncio.gather(*(coro for _, coro in sources), return_exceptions=True)

    merged = []
    for (source_name, _), result in zip(sources, settled):
        if isinstance(result, Exception):
            _log(result_store, job_id, f"{source_name} rejected: {repr(result)}", "error")
            continue
        if isinstance(result, list):
            _log(result_store, job_id, f"{source_name} fulfilled with {len(result)} parsed results")
            merged.extend(result)
        else:
            _log(result_store, job_id, f"{source_name} returned non-list result: {type(result)}", "error")

    _log(result_store, job_id, f"merged length before dedupe/filter = {len(merged)}")

    seen = set()
    unique = []
    for item in merged:
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        if not title or not url.startswith("http") or url in seen:
            continue
        seen.add(url)
        item["title"] = title
        item["url"] = url
        item.setdefault("domain", urlparse(url).netloc)
        item.setdefault("source_domain", item["domain"])
        item.setdefault("price", None)
        unique.append(item)

    _log(result_store, job_id, f"final deduped http-only length after primary sources = {len(unique)}")

    if len(unique) < 10:
        _log(result_store, job_id, "primary sources returned fewer than 10 results; starting DuckDuckGo Lite real-web fallback")
        try:
            fallback_results = await duckduckgo_lite_fallback(query, job_id, result_store)
            _log(result_store, job_id, f"DuckDuckGo Lite fallback fulfilled with {len(fallback_results)} parsed results")
            for item in fallback_results:
                url = (item.get("url") or "").strip()
                if not url.startswith("http") or url in seen:
                    continue
                seen.add(url)
                unique.append(item)
        except Exception as exc:
            _log(result_store, job_id, f"DuckDuckGo Lite fallback rejected: {repr(exc)}", "error")

    _log(result_store, job_id, f"final deduped http-only length = {len(unique)}")
    return unique


def build_wikipedia_query(query: str, intent: dict | None = None) -> str:
    search_queries = (intent or {}).get("searchQueries") or []
    return search_queries[0] if search_queries else ((intent or {}).get("topic") or query)


def build_reddit_query(query: str, intent: dict | None = None) -> str:
    search_queries = (intent or {}).get("searchQueries") or []
    if len(search_queries) > 1:
        return search_queries[1]
    keywords = [str(word).lower() for word in (intent or {}).get("keywords", [])]
    return " ".join(keywords[:5]) if keywords else query


async def wikipedia_search(query: str, job_id: str = "", result_store=None) -> list[dict]:
    _log(result_store, job_id, "Wikipedia fetch start")
    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        response = await client.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 8,
                "origin": "*",
            },
            headers=COMMON_HEADERS,
        )
    _log(result_store, job_id, f"Wikipedia raw response length = {len(response.text)} status={response.status_code}")
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("query", {}).get("search", []):
        title = item.get("title", "")
        snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
        if not title:
            continue
        results.append({
            "title": title,
            "url": "https://en.wikipedia.org/wiki/" + quote(title.replace(" ", "_"), safe=""),
            "description": snippet,
            "snippet": snippet,
            "relevance_score": 60,
            "category": "article",
            "source": "wikipedia",
        })
    return results


async def reddit_search(query: str, job_id: str = "", result_store=None) -> list[dict]:
    _log(result_store, job_id, "Reddit fetch start")
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            response = await client.get(
                "https://www.reddit.com/search.json",
                params={"q": query, "limit": 8, "sort": "relevance", "raw_json": 1},
                headers={**COMMON_HEADERS, **REDDIT_HEADERS, "Accept": "application/json"},
            )
        _log(result_store, job_id, f"Reddit raw response length = {len(response.text)} status={response.status_code}")
        
        if response.status_code == 403:
            _log(result_store, job_id, "Reddit blocked request (403), skipping", "error")
            return []
        
        response.raise_for_status()
        data = response.json()

        results = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            title = post.get("title", "")
            permalink = post.get("permalink", "")
            if not title or not permalink:
                continue
            description = (post.get("selftext") or title)[:200]
            results.append({
                "title": title,
                "url": "https://www.reddit.com" + permalink,
                "description": description,
                "snippet": title,
                "relevance_score": 50,
                "category": "forum",
                "source": "reddit",
            })
        return results
    except Exception as e:
        _log(result_store, job_id, f"Reddit error: {str(e)}", "error")
        return []


async def hackernews_search(query: str, job_id: str = "", result_store=None) -> list[dict]:
    _log(result_store, job_id, "HackerNews fetch start")
    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        response = await client.get(
            "http://hn.algolia.com/api/v1/search",
            params={"query": query, "tags": "story", "hitsPerPage": 8},
        )
    _log(result_store, job_id, f"HackerNews raw response length = {len(response.text)} status={response.status_code}")
    response.raise_for_status()
    data = response.json()

    results = []
    for hit in data.get("hits", []):
        title = hit.get("title") or ""
        if not title:
            continue
        url = hit.get("url")
        if not url:
            continue
        description = title
        results.append({
            "title": title,
            "url": url,
            "description": description,
            "snippet": title,
            "relevance_score": 55,
            "category": "article",
            "source": "hackernews",
        })
    return results


async def duckduckgo_instant_search(query: str, job_id: str = "", result_store=None) -> list[dict]:
    _log(result_store, job_id, "DuckDuckGo instant answer fetch start")
    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        response = await client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            headers=DDG_HEADERS,
    )
    _log(result_store, job_id, f"DuckDuckGo instant raw response length = {len(response.text)} status={response.status_code}")
    response.raise_for_status()
    data = response.json()

    topics = _flatten_duckduckgo_topics(data.get("RelatedTopics", []))
    results = []
    for topic in topics:
        first_url = topic.get("FirstURL")
        text = topic.get("Text")
        if not first_url or not text:
            continue
        results.append({
            "title": text[:80],
            "url": first_url,
            "description": text,
            "snippet": text,
            "relevance_score": 45,
            "category": "article",
            "source": "duckduckgo_instant",
        })
        if len(results) >= 8:
            break
    return results


async def openai_search_suggestions(query: str, job_id: str = "", result_store=None) -> list[dict]:
    _log(result_store, job_id, "OpenAI search suggestions fetch start")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a search engine. Given a query return a JSON array of 5 relevant results "
                            "each with title, url, description fields. Only return real existing URLs. "
                            "Return only valid JSON array nothing else."
                        ),
                    },
                    {"role": "user", "content": query},
                ],
                "temperature": 0.1,
                "max_tokens": 1200,
            },
        )
    _log(result_store, job_id, f"OpenAI raw response length = {len(response.text)} status={response.status_code}")
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"].strip()
    if "```" in text:
        text = text[text.find("["):text.rfind("]") + 1]
    data = json.loads(text)
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
            "snippet": item.get("description", ""),
            "relevance_score": 50,
            "category": "article",
            "source": "openai",
        }
        for item in data[:5]
        if isinstance(item, dict)
    ]


async def serpapi_search(query: str, job_id: str = "", result_store=None) -> list[dict]:
    _log(result_store, job_id, "SerpAPI fetch start")
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(
            "https://serpapi.com/search.json",
            params={"q": query, "api_key": os.environ.get("SERPAPI_KEY"), "num": 8},
        )
    _log(result_store, job_id, f"SerpAPI raw response length = {len(response.text)} status={response.status_code}")
    response.raise_for_status()
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "description": item.get("snippet", ""),
            "snippet": item.get("snippet", ""),
            "relevance_score": 65,
            "category": "article",
            "source": "serpapi",
        }
        for item in response.json().get("organic_results", [])[:8]
    ]


async def brave_search(query: str, job_id: str = "", result_store=None) -> list[dict]:
    _log(result_store, job_id, "Brave fetch start")
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": 8},
            headers={"X-Subscription-Token": os.environ.get("BRAVE_API_KEY", "")},
        )
    _log(result_store, job_id, f"Brave raw response length = {len(response.text)} status={response.status_code}")
    response.raise_for_status()
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
            "snippet": item.get("description", ""),
            "relevance_score": 65,
            "category": "article",
            "source": "brave",
        }
        for item in response.json().get("web", {}).get("results", [])[:8]
    ]


async def google_search(query: str, job_id: str = "", result_store=None) -> list[dict]:
    search_engine_id = os.environ.get("GOOGLE_CSE_ID") or os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
    if not search_engine_id:
        _log(result_store, job_id, "Google API key present but GOOGLE_CSE_ID is missing", "error")
        return []
    _log(result_store, job_id, "Google fetch start")
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"q": query, "key": os.environ.get("GOOGLE_API_KEY"), "cx": search_engine_id, "num": 8},
        )
    _log(result_store, job_id, f"Google raw response length = {len(response.text)} status={response.status_code}")
    response.raise_for_status()
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "description": item.get("snippet", ""),
            "snippet": item.get("snippet", ""),
            "relevance_score": 65,
            "category": "article",
            "source": "google",
        }
        for item in response.json().get("items", [])[:8]
    ]


async def bing_search(query: str, job_id: str = "", result_store=None) -> list[dict]:
    _log(result_store, job_id, "Bing fetch start")
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(
            "https://api.bing.microsoft.com/v7.0/search",
            params={"q": query, "count": 8},
            headers={"Ocp-Apim-Subscription-Key": os.environ.get("BING_API_KEY", "")},
        )
    _log(result_store, job_id, f"Bing raw response length = {len(response.text)} status={response.status_code}")
    response.raise_for_status()
    return [
        {
            "title": item.get("name", ""),
            "url": item.get("url", ""),
            "description": item.get("snippet", ""),
            "snippet": item.get("snippet", ""),
            "relevance_score": 65,
            "category": "article",
            "source": "bing",
        }
        for item in response.json().get("webPages", {}).get("value", [])[:8]
    ]


async def duckduckgo_lite_fallback(query: str, job_id: str = "", result_store=None) -> list[dict]:
    _log(result_store, job_id, "DuckDuckGo Lite fallback fetch start")
    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
        response = await client.get(
            "https://lite.duckduckgo.com/lite/",
            params={"q": query},
            headers=COMMON_HEADERS,
        )
    _log(result_store, job_id, f"DuckDuckGo Lite fallback raw response length = {len(response.text)} status={response.status_code}")
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for link in soup.select("table tr a.result-link"):
        row = link.find_parent("tr")
        title = link.get_text(" ", strip=True)
        href = _normalize_duckduckgo_url(link.get("href", ""))
        snippet = None
        next_row = row.find_next_sibling("tr") if row else None
        while next_row:
            snippet = next_row.select_one(".result-snippet")
            if snippet or next_row.select_one("a.result-link"):
                break
            next_row = next_row.find_next_sibling("tr")
        description = snippet.get_text(" ", strip=True) if snippet else title
        if title and href:
            results.append({
                "title": title,
                "url": href,
                "description": description,
                "snippet": description,
                "relevance_score": 60,
                "category": "article",
                "source": "duckduckgo_lite",
                "domain": urlparse(href).netloc,
                "source_domain": urlparse(href).netloc,
                "price": None,
            })
    return results


async def bing_html_search(query: str, job_id: str = "", result_store=None) -> list[dict]:
    _log(result_store, job_id, "Bing HTML fetch start")
    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
        response = await client.get(
            "https://www.bing.com/search",
            params={"q": query, "count": 10},
            headers={"User-Agent": "Mozilla/5.0"},
        )
    _log(result_store, job_id, f"Bing HTML raw response length = {len(response.text)} status={response.status_code}")
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for item in soup.select("li.b_algo"):
        link = item.select_one("h2 a")
        if not link:
            continue
        title = link.get_text(" ", strip=True)
        href = _normalize_bing_url(link.get("href", ""))
        snippet_node = item.select_one(".b_caption p")
        description = snippet_node.get_text(" ", strip=True) if snippet_node else title
        if title and href.startswith("http"):
            results.append({
                "title": title,
                "url": href,
                "description": description,
                "snippet": description,
                "relevance_score": 65,
                "category": "article",
                "source": "bing_html",
                "domain": urlparse(href).netloc,
                "source_domain": urlparse(href).netloc,
                "price": None,
            })
        if len(results) >= 10:
            break
    return results


def _flatten_duckduckgo_topics(topics: list) -> list[dict]:
    flattened = []
    for topic in topics:
        if "Topics" in topic:
            flattened.extend(_flatten_duckduckgo_topics(topic.get("Topics", [])))
        else:
            flattened.append(topic)
    return flattened


def _normalize_duckduckgo_url(href: str) -> str:
    href = urljoin("https://lite.duckduckgo.com/lite/", href or "")
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and "uddg=" in parsed.query:
        for part in parsed.query.split("&"):
            if part.startswith("uddg="):
                return unquote(part.split("=", 1)[1])
    return href


def _normalize_bing_url(href: str) -> str:
    parsed = urlparse(href or "")
    if "bing.com" in parsed.netloc and parsed.path.startswith("/ck/"):
        target = parse_qs(parsed.query).get("u", [""])[0]
        if target.startswith("a1"):
            try:
                import base64
                padded = target[2:] + "=" * (-len(target[2:]) % 4)
                decoded = base64.urlsafe_b64decode(padded).decode("utf-8", errors="ignore")
                if decoded.startswith("http"):
                    return decoded
            except Exception:
                return href
    return href or ""
