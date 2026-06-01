import asyncio
import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import AsyncOpenAI
from services.supabase_client import save_results, update_session_status

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


async def run_ui_formatter(job_id: str, qa_results: list, query: str, result_store) -> str:
    print(f"[Formatter] received {len(qa_results)} results from QA", flush=True)
    result_store.add_log(job_id, "UIFormatter", "start", f"Formatting {len(qa_results)} results")

    if not qa_results:
        result_store.add_log(job_id, "UIFormatter", "error", "No results to format")
        print("[Formatter] No results received from QA agent", flush=True)
        return f"<p>No results found for: <strong>{query}</strong></p>"

    enriched_results = await enrich_results(qa_results[:20], result_store, job_id)
    formatted_results = []
    for idx, result in enumerate(enriched_results):
        url = result.get("url", "")
        try:
            source_domain = urlparse(url).netloc
        except Exception:
            source_domain = ""
        formatted_results.append({
            "session_id": job_id,
            "title": result.get("title", ""),
            "url": url,
            "description": result.get("description") or result.get("snippet") or result.get("summary", ""),
            "snippet": result.get("snippet") or result.get("description") or "",
            "source_domain": result.get("source_domain") or result.get("domain") or source_domain,
            "domain": result.get("domain") or source_domain,
            "favicon_url": result.get("favicon_url") or (f"https://www.google.com/s2/favicons?domain={source_domain}&sz=32" if source_domain else ""),
            "og_image": result.get("og_image") or result.get("image") or "",
            "price": result.get("price") or "",
            "relevance_score": result.get("relevance_score", 0),
            "rank": result.get("rank", idx + 1),
            "category": result.get("category", "article"),
            "is_product_page": bool(result.get("is_product_page") or result.get("price")),
            "is_verified": result.get("is_verified", True),
        })

    result_store.set_results(job_id, formatted_results)
    try:
        await save_results(job_id, {"results": formatted_results})
        await update_session_status(job_id, "complete")
    except Exception as e:
        message = (
            "Supabase insert failed. Ensure results table has columns: "
            "session_id, title, url, description, snippet, source_domain, "
            "relevance_score, rank, category, is_verified, og_image, price. "
            f"Error: {e}"
        )
        print(f"[Formatter] {message}", flush=True)
        result_store.add_log(job_id, "UIFormatter", "error", message)

    result_store.add_log(job_id, "UIFormatter", "info", f"results:ready count={len(formatted_results)}")
    print(f"[Formatter] Sent {len(formatted_results)} results to frontend", flush=True)

    api_key = os.environ.get("OPENAI_API_KEY", "")

    if api_key and api_key.startswith("sk-"):
        try:
            output = await openai_format(qa_results, query, api_key)
            print(f"[Formatter] OpenAI formatting complete, output length: {len(output)}", flush=True)
            result_store.add_log(job_id, "UIFormatter", "info", "OpenAI formatting complete")
            result_store.add_log(job_id, "UIFormatter", "complete", "Formatting complete")
            return output
        except Exception as e:
            print(f"[Formatter] OpenAI formatting failed: {str(e)}, using fallback", flush=True)
            result_store.add_log(job_id, "UIFormatter", "error", f"OpenAI formatting failed: {str(e)}, using fallback")

    print(f"[Formatter] Using fallback formatting for {len(qa_results)} results", flush=True)
    
    # Create a better fallback format
    summary = f"Found {len(qa_results)} results for your query."
    items = []
    
    for r in formatted_results:
        title = r.get('title', 'Untitled')
        url = r.get('url', '#')
        description = r.get('description') or r.get('snippet') or r.get('summary', '')
        source = r.get('source_domain') or r.get('source', 'web')
        score = r.get('relevance_score', 0)
        price = r.get('price')
        
        item = f"<li><strong>{title}</strong><br>"
        if price:
            item += f"{price}<br>"
        if description:
            item += f"{description[:200]}<br>"
        item += f"<a href='{url}' target='_blank'>{source}</a>"
        if score:
            item += f" (score: {score:.0f})"
        item += "</li>"
        items.append(item)
    
    result_store.add_log(job_id, "UIFormatter", "complete", f"Fallback formatting complete: {len(items)} items")
    return f"<p>{summary}</p><ol>{''.join(items)}</ol>"


async def enrich_results(results: list, result_store, job_id: str) -> list:
    semaphore = asyncio.Semaphore(5)

    async def enrich_one(result: dict) -> dict:
        url = result.get("url", "")
        if not url.startswith("http"):
            return result
        async with semaphore:
            try:
                metadata = await scrape_result_metadata(url)
                return {**result, **{key: value for key, value in metadata.items() if value}}
            except Exception as e:
                if result_store:
                    result_store.add_log(job_id, "UIFormatter", "info", f"Metadata scrape skipped for {url}: {e}")
                return result

    enriched = await asyncio.gather(*(enrich_one(result) for result in results), return_exceptions=True)
    output = []
    for original, item in zip(results, enriched):
        output.append(original if isinstance(item, Exception) else item)
    image_count = sum(1 for item in output if item.get("og_image") or item.get("image"))
    price_count = sum(1 for item in output if item.get("price"))
    print(f"[Formatter] Enriched metadata: images={image_count} prices={price_count}", flush=True)
    if result_store:
        result_store.add_log(job_id, "UIFormatter", "info", f"Enriched metadata: images={image_count} prices={price_count}")
    return output


async def scrape_result_metadata(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 MARAS-Bot/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        return {}
    response.raise_for_status()

    soup = BeautifulSoup(response.text[:600000], "html.parser")
    image = extract_image(soup, str(response.url))
    price = extract_price(soup)
    product_title = extract_product_title(soup)
    return {
        "og_image": image,
        "price": price,
        "product_title": product_title,
        "is_product_page": bool(price),
    }


def extract_product_title(soup: BeautifulSoup) -> str:
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        name = find_jsonld_product_name(data)
        if name:
            return name
    meta = soup.select_one('meta[property="og:title"], meta[name="twitter:title"]')
    value = meta.get("content", "").strip() if meta else ""
    return value[:160]


def extract_image(soup: BeautifulSoup, base_url: str) -> str:
    selectors = [
        ('meta[property="og:image"]', "content"),
        ('meta[property="og:image:secure_url"]', "content"),
        ('meta[name="twitter:image"]', "content"),
        ('meta[name="twitter:image:src"]', "content"),
        ('link[rel="image_src"]', "href"),
    ]
    for selector, attr in selectors:
        tag = soup.select_one(selector)
        value = tag.get(attr, "").strip() if tag else ""
        if value:
            return urljoin(base_url, value)

    for img in soup.select("img"):
        value = (img.get("src") or img.get("data-src") or "").strip()
        alt = (img.get("alt") or "").lower()
        if value and not any(skip in value.lower() + alt for skip in ["logo", "icon", "avatar", "sprite"]):
            return urljoin(base_url, value)
    return ""


def extract_price(soup: BeautifulSoup) -> str:
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        price = find_jsonld_price(data)
        if price:
            return price

    selectors = [
        'meta[property="product:price:amount"]',
        'meta[property="og:price:amount"]',
        'meta[itemprop="price"]',
        '[itemprop="price"]',
        '[class*="price" i]',
        '[id*="price" i]',
    ]
    for selector in selectors:
        tag = soup.select_one(selector)
        if not tag:
            continue
        value = tag.get("content") or tag.get_text(" ", strip=True)
        price = normalize_price(value)
        if price:
            return price

    body_text = soup.get_text(" ", strip=True)[:5000]
    match = re.search(r"(?:₹|Rs\.?|\$|€|£)\s?\d[\d,]*(?:\.\d{1,2})?", body_text)
    return match.group(0) if match else ""


def find_jsonld_price(data) -> str:
    if isinstance(data, list):
        for item in data:
            price = find_jsonld_price(item)
            if price:
                return price
    if not isinstance(data, dict):
        return ""

    offers = data.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    if isinstance(offers, dict):
        amount = offers.get("price") or offers.get("lowPrice") or offers.get("highPrice")
        currency = offers.get("priceCurrency") or data.get("priceCurrency") or ""
        if amount:
            return normalize_price(f"{currency} {amount}".strip())

    for value in data.values():
        if isinstance(value, (dict, list)):
            price = find_jsonld_price(value)
            if price:
                return price
    return ""


def find_jsonld_product_name(data) -> str:
    if isinstance(data, list):
        for item in data:
            name = find_jsonld_product_name(item)
            if name:
                return name
    if not isinstance(data, dict):
        return ""

    item_type = data.get("@type")
    item_types = item_type if isinstance(item_type, list) else [item_type]
    if any(str(value).lower() == "product" for value in item_types):
        name = str(data.get("name") or "").strip()
        if name:
            return name[:160]

    for value in data.values():
        if isinstance(value, (dict, list)):
            name = find_jsonld_product_name(value)
            if name:
                return name
    return ""


def normalize_price(value) -> str:
    if isinstance(value, bool):
        return ""
    text = str(value or "").strip()
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    currency_symbols = {
        "USD": "$",
        "INR": "₹",
        "EUR": "€",
        "GBP": "£",
    }
    for code, symbol in currency_symbols.items():
        text = re.sub(rf"\b{code}\b\s*", symbol, text, flags=re.IGNORECASE)
    match = re.search(r"(?:₹|Rs\.?|\$|€|£)?\s?\d[\d,]*(?:\.\d{1,2})?", text)
    if not match:
        return ""
    price = match.group(0).strip()
    if len(price) > 24:
        return ""
    return price


async def openai_format(results: list, query: str, api_key: str) -> str:
    client = AsyncOpenAI(api_key=api_key)
    results_json = json.dumps(results[:10])
    response = await asyncio.wait_for(
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Format search results as clean readable HTML. "
                        "Structure your response exactly like this: "
                        "1. Opening <p> with a 2-sentence summary "
                        "   of findings for the query. "
                        "2. <ol> with one <li> per result containing: "
                        "   <strong>title</strong>, price if available, "
                        "   brief description, "
                        "   <a href='url'>source</a>. "
                        "Use only these tags: p ol li strong a br. "
                        "No CSS. No classes. No scripts. No markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Query: {query}\n\nResults: {results_json}",
                },
            ],
            temperature=0.4,
            max_tokens=1500,
        ),
        timeout=45.0,
    )
    return response.choices[0].message.content.strip()
