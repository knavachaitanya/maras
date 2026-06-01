import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import httpx
from urllib.parse import urlparse, quote_plus
from config import settings
import logging
import os

SEARCH_ENGINES = {
    "google":     "https://www.google.com/search?q={q}&num=5",
    "bing":       "https://www.bing.com/search?q={q}",
    "duckduckgo": "https://html.duckduckgo.com/html/?q={q}",
}

async def tavily_search(query: str, max_results: int = 10) -> list[dict]:
    """Search using Tavily API if key is available."""
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return []
    
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                    "include_answer": False
                }
            )
            
            if response.status_code != 200:
                logging.warning(f"Tavily API returned status {response.status_code}")
                return []
            
            data = response.json()
            results = []
            
            for r in data.get("results", []):
                url = r.get("url", "")
                title = r.get("title", "")
                snippet = r.get("content", "")
                
                # Only include results with real content
                if url and title and snippet and url.startswith("http"):
                    results.append({
                        "url": url,
                        "title": title,
                        "snippet": snippet,
                        "source": "tavily"
                    })
            
            return results
    except Exception as e:
        logging.warning(f"Tavily search failed: {e}")
        return []

async def google_httpx_search(query: str, max_results: int = 10) -> list[dict]:
    """Search Google using httpx with proper headers."""
    try:
        from urllib.parse import quote_plus
        import re
        
        q = quote_plus(query)
        url = f"https://www.google.com/search?q={q}&num={max_results}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"Google httpx returned status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            
            # Try to find search result divs
            for g in soup.select("div.g, div[data-sokoban-container]"):
                # Extract title
                title_elem = g.select_one("h3")
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                
                # Extract URL
                link_elem = g.select_one("a[href]")
                if not link_elem:
                    continue
                href = link_elem.get("href", "")
                
                # Clean URL
                if href.startswith("/url?q="):
                    url_match = re.search(r'/url\?q=([^&]+)', href)
                    if url_match:
                        from urllib.parse import unquote
                        actual_url = unquote(url_match.group(1))
                    else:
                        continue
                elif href.startswith("http"):
                    actual_url = href
                else:
                    continue
                
                # Skip Google's own URLs
                if "google.com" in actual_url:
                    continue
                
                # Extract snippet
                snippet_elem = g.select_one("div[data-sncf], div.VwiC3b, span.aCOpRe")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else title
                
                if actual_url and title:
                    results.append({
                        "url": actual_url,
                        "title": title,
                        "snippet": snippet,
                        "source": "google_httpx"
                    })
                    
                    if len(results) >= max_results:
                        break
            
            return results
    except Exception as e:
        logging.warning(f"Google httpx search failed: {e}")
        return []

async def duckduckgo_search(query: str, max_results: int = 10) -> list[dict]:
    """Search using DuckDuckGo via duckduckgo-search package."""
    try:
        from duckduckgo_search import DDGS
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def _sync_search():
            results = []
            try:
                # Try multiple backends
                for backend in ["api", "html", "lite"]:
                    try:
                        ddgs = DDGS(timeout=20)
                        search_results = list(ddgs.text(query, max_results=max_results, backend=backend))
                        
                        if search_results:
                            for r in search_results:
                                title = r.get("title", "")
                                url = r.get("href", "")
                                snippet = r.get("body", "")
                                
                                # Only include results with real content
                                if url and title and snippet and url.startswith("http"):
                                    results.append({
                                        "url": url,
                                        "title": title,
                                        "snippet": snippet,
                                        "source": "duckduckgo"
                                    })
                                    
                                    if len(results) >= max_results:
                                        break
                            
                            if results:
                                print(f"DuckDuckGo {backend} backend succeeded")
                                break
                    except Exception as e:
                        print(f"DuckDuckGo {backend} backend failed: {e}")
                        continue
                        
            except Exception as e:
                logging.warning(f"DuckDuckGo sync search error: {e}")
            return results
        
        # Run synchronous search in thread pool
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            results = await loop.run_in_executor(executor, _sync_search)
        
        return results
    except Exception as e:
        logging.warning(f"DuckDuckGo search failed: {e}")
        return []

async def serpapi_search(query: str, max_results: int = 10) -> list[dict]:
    """Search using SerpAPI if key is available."""
    api_key = os.environ.get("SERPAPI_KEY", "")
    if not api_key:
        return []
    
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                "https://serpapi.com/search",
                params={
                    "q": query,
                    "api_key": api_key,
                    "num": max_results,
                    "engine": "google"
                }
            )
            
            if response.status_code != 200:
                logging.warning(f"SerpAPI returned status {response.status_code}")
                return []
            
            data = response.json()
            results = []
            
            for r in data.get("organic_results", []):
                url = r.get("link", "")
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                
                # Only include results with real content
                if url and title and url.startswith("http"):
                    results.append({
                        "url": url,
                        "title": title,
                        "snippet": snippet or title,
                        "source": "serpapi"
                    })
            
            return results[:max_results]
    except Exception as e:
        logging.warning(f"SerpAPI search failed: {e}")
        return []

async def search_web(query: str, engines: list[str]) -> list[dict]:
    """Search web with multiple fallback methods in priority order."""
    results = []
    method_used = None
    
    # Priority 1: Playwright (works reliably, extracts titles and snippets)
    try:
        print(f"Attempting Playwright search for: {query}")
        results = await playwright_search(query, engines)
        if results:
            method_used = "Playwright"
            print(f"[OK] Found {len(results)} results using Playwright")
            return results
        else:
            print("[FAILED] Playwright returned no results")
    except Exception as e:
        print(f"[ERROR] Playwright search failed: {e}")
    
    # Priority 2: Google httpx (no API key needed, fast)
    try:
        print(f"Attempting Google httpx search for: {query}")
        results = await google_httpx_search(query, max_results=10)
        if results:
            method_used = "Google httpx"
            print(f"[OK] Found {len(results)} results using Google httpx")
            return results
        else:
            print("[FAILED] Google httpx returned no results")
    except Exception as e:
        print(f"[ERROR] Google httpx search failed: {e}")
    
    # Priority 3: Tavily (if API key exists)
    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    if tavily_key:
        try:
            print(f"Attempting Tavily search for: {query}")
            results = await tavily_search(query, max_results=10)
            if results:
                method_used = "Tavily API"
                print(f"[OK] Found {len(results)} results using Tavily")
                return results
            else:
                print("[FAILED] Tavily returned no results")
        except Exception as e:
            print(f"[ERROR] Tavily search failed: {e}")
    
    # Priority 4: DuckDuckGo (no API key needed)
    try:
        print(f"Attempting DuckDuckGo search for: {query}")
        results = await duckduckgo_search(query, max_results=10)
        if results:
            method_used = "DuckDuckGo"
            print(f"[OK] Found {len(results)} results using DuckDuckGo")
            return results
        else:
            print("[FAILED] DuckDuckGo returned no results")
    except Exception as e:
        print(f"[ERROR] DuckDuckGo search failed: {e}")
    
    # Priority 5: SerpAPI (if API key exists)
    serpapi_key = os.environ.get("SERPAPI_KEY", "")
    if serpapi_key:
        try:
            print(f"Attempting SerpAPI search for: {query}")
            results = await serpapi_search(query, max_results=10)
            if results:
                method_used = "SerpAPI"
                print(f"[OK] Found {len(results)} results using SerpAPI")
                return results
            else:
                print("[FAILED] SerpAPI returned no results")
        except Exception as e:
            print(f"[ERROR] SerpAPI search failed: {e}")
    
    print(f"[ERROR] All search methods failed for query: {query}")
    return []

async def playwright_search(query: str, engines: list[str]) -> list[dict]:
    """Use Playwright to scrape search engine result pages."""
    results = []
    q = quote_plus(query)
    engines = ["google"]

    try:
        async with async_playwright() as pw:
            try:
                browser = await pw.chromium.launch(headless=True)
            except Exception as e:
                print(f"Failed to launch browser: {e}")
                return []
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            for engine in engines:
                url = SEARCH_ENGINES[engine].format(q=q)
                try:
                    page = await context.new_page()
                    await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                    await asyncio.sleep(1)
                    html = await page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    if engine == "google":
                        # Try to extract results with titles and snippets
                        for a in soup.select("a"):
                            href = a.get("href", "")
                            
                            # Find h3 within the link
                            h3 = a.select_one("h3")
                            if not h3:
                                continue
                            
                            title = h3.get_text(strip=True)
                            if not title:
                                continue
                            
                            # Extract URL
                            if href.startswith("/url?q="):
                                actual_url = href.split("/url?q=")[1].split("&")[0]
                            elif href.startswith("http"):
                                actual_url = href
                            else:
                                continue
                            
                            # Skip Google's own URLs
                            if "google.com" in actual_url or "youtube.com" in actual_url:
                                continue
                            
                            # Try to find snippet - look for nearby text
                            snippet = ""
                            parent = a.find_parent()
                            if parent:
                                # Look for divs with text content near the link
                                for sibling in parent.find_all_next(["div", "span"], limit=5):
                                    text = sibling.get_text(strip=True)
                                    if text and len(text) > 50 and text != title:
                                        snippet = text
                                        break
                            
                            if not snippet:
                                snippet = title
                            
                            results.append({
                                "url": actual_url,
                                "title": title,
                                "snippet": snippet[:300],
                                "source": "playwright"
                            })
                            
                            if len(results) >= 10:
                                break
                    
                    await page.close()
                except Exception as e:
                    print(f"Search engine {engine} error: {e}")
                    continue
            
            await browser.close()
    except Exception as e:
        print(f"Playwright error: {e}")
        return []
    
    # Remove duplicates
    seen = set()
    unique_results = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique_results.append(r)
    
    return unique_results[:10]

async def scrape_urls(urls: list[str], query: str) -> list[dict]:
    """Scrape each URL and extract structured content."""
    async def scrape_one(url: str) -> dict | None:
        try:
            async with httpx.AsyncClient(
                timeout=settings.SCRAPE_TIMEOUT_SECONDS, 
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            ) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return None
                
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Extract title
                title = soup.find("title")
                title_text = title.text.strip() if title else ""
                
                # Extract meta description
                desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
                description = desc_tag.get("content", "").strip() if desc_tag else ""
                
                # Extract OG image
                og_img = soup.find("meta", property="og:image")
                og_image = og_img.get("content") if og_img else None
                
                # Extract main content
                main_content = soup.find("main") or soup.find("article") or soup.find("body")
                if main_content:
                    body_text = " ".join(main_content.get_text(separator=" ").split())
                else:
                    body_text = " ".join(soup.get_text(separator=" ").split())
                
                # Limit content snippet
                content_snippet = body_text[:1000] if body_text else ""
                
                # Use content snippet as description if no meta description
                if not description and content_snippet:
                    description = content_snippet[:300]
                
                domain = urlparse(url).netloc
                
                # Skip if no meaningful content
                if not title_text and not description and not content_snippet:
                    return None
                
                return {
                    "url": url,
                    "title": title_text or domain,
                    "description": description or content_snippet[:200],
                    "content_snippet": content_snippet,
                    "source_domain": domain,
                    "og_image": og_image,
                    "scraped_at": __import__("datetime").datetime.utcnow().isoformat(),
                }
        except Exception as e:
            print(f"Scrape error for {url}: {e}")
            return None

    # Limit concurrent scraping to 8 URLs for speed
    max_urls = min(len(urls), 8)
    tasks = [scrape_one(url) for url in urls[:max_urls]]
    results = await asyncio.gather(*tasks)
    
    # Filter out None results
    valid_results = [r for r in results if r is not None]
    
    print(f"Scraped {len(valid_results)} out of {max_urls} URLs")
    
    return valid_results

