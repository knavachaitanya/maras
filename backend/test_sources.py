import httpx
import asyncio

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

async def test():
    print("Testing data sources...")
    
    # Test Wikipedia
    try:
        r = await httpx.AsyncClient(timeout=8.0, follow_redirects=True).get(
            'https://en.wikipedia.org/w/api.php',
            params={
                'action':'query',
                'list':'search',
                'srsearch':'phones under 80000',
                'format':'json',
                'srlimit':5,
                'origin':'*'
            },
            headers=HEADERS
        )
        print(f'Wikipedia status: {r.status_code}')
        results = r.json().get('query',{}).get('search',[])
        print(f'Wikipedia: {len(results)} results')
    except Exception as e:
        print(f'Wikipedia: ERROR - {e}')
    
    # Test Reddit
    try:
        r = await httpx.AsyncClient(timeout=8.0, follow_redirects=True).get(
            'https://www.reddit.com/search.json',
            params={'q':'phones under 80000','limit':5,'sort':'relevance'},
            headers=HEADERS
        )
        print(f'Reddit status: {r.status_code}')
        results = r.json().get('data',{}).get('children',[])
        print(f'Reddit: {len(results)} results')
    except Exception as e:
        print(f'Reddit: ERROR - {e}')
    
    # Test HackerNews
    try:
        r = await httpx.AsyncClient(timeout=8.0, follow_redirects=True).get(
            'http://hn.algolia.com/api/v1/search',
            params={'query':'phones under 80000','hitsPerPage':5}
        )
        print(f'HackerNews status: {r.status_code}')
        results = r.json().get('hits',[])
        print(f'HackerNews: {len(results)} results')
    except Exception as e:
        print(f'HackerNews: ERROR - {e}')
    
    # Test DuckDuckGo Lite
    try:
        r = await httpx.AsyncClient(timeout=12.0, follow_redirects=True).get(
            'https://lite.duckduckgo.com/lite/',
            params={'q':'phones under 80000'},
            headers=HEADERS
        )
        print(f'DuckDuckGo Lite status: {r.status_code}')
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.select('a.result-link')
        print(f'DuckDuckGo Lite: {len(links)} results')
    except Exception as e:
        print(f'DuckDuckGo Lite: ERROR - {e}')

asyncio.run(test())
