"""Test script to debug search functionality."""
import requests
import json
import time

API_URL = "http://127.0.0.1:8000"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"✅ Health check: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_search(query="test query", fast_mode=True):
    """Test search endpoint."""
    print(f"\nTesting search with query: '{query}'")
    try:
        response = requests.post(
            f"{API_URL}/api/search",
            json={"query": query, "fast_mode": fast_mode},
            timeout=10
        )
        data = response.json()
        print(f"✅ Search initiated: {json.dumps(data, indent=2)}")
        return data.get("session_id")
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return None

def test_results(session_id):
    """Test results endpoint."""
    print(f"\nFetching results for session: {session_id}")
    try:
        # Poll for results
        for i in range(10):
            response = requests.get(f"{API_URL}/api/results/{session_id}", timeout=5)
            data = response.json()
            status = data.get("status")
            results_count = len(data.get("results", []))
            
            print(f"  Poll {i+1}: status={status}, results={results_count}")
            
            if status in ["complete", "completed", "error"]:
                print(f"\n✅ Final status: {status}")
                print(f"   Results: {results_count}")
                if results_count > 0:
                    print(f"\n   First result:")
                    print(f"   - Title: {data['results'][0].get('title')}")
                    print(f"   - URL: {data['results'][0].get('url')}")
                return data
            
            time.sleep(1)
        
        print("⚠️  Timeout waiting for results")
        return None
    except Exception as e:
        print(f"❌ Results fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("=" * 60)
    print("MARAS Search Test")
    print("=" * 60)
    
    # Test health
    if not test_health():
        print("\n❌ Backend is not responding. Make sure it's running:")
        print("   cd backend && python start.py")
        return
    
    # Test search
    session_id = test_search("laptops under 74000 rupees", fast_mode=True)
    if not session_id:
        print("\n❌ Search request failed")
        return
    
    # Test results
    results = test_results(session_id)
    if not results:
        print("\n❌ Failed to get results")
        return
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
