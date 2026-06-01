import asyncio
from services.scraper import duckduckgo_search
import httpx
from bs4 import BeautifulSoup

async def test():
    # Test direct HTTP request
    query = "best laptops 2024"
    url = f"https://html.duckduckgo.com/html/"
    
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            url,
            data={"q": query, "b": "", "kl": "us-en"},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        
        print(f"Status: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        result_divs = soup.select(".result")
        print(f"Found {len(result_divs)} result divs")
        
        if result_divs:
            first = result_divs[0]
            print(f"First result HTML: {str(first)[:200]}")
    
    # Test function
    results = await duckduckgo_search(query, 3)
    print(f"\nFunction returned {len(results)} results")
    for r in results[:2]:
        print(f"{r['title'][:50]}... - {r['url'][:50]}...")

asyncio.run(test())

