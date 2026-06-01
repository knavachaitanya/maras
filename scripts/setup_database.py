"""Setup and verify Supabase database tables."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

def check_tables():
    """Check if all required tables exist."""
    print("=" * 60)
    print("Checking Supabase Database Tables")
    print("=" * 60)
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print(" Missing Supabase credentials in .env file")
        return False
    
    print(f"\n Supabase URL: {SUPABASE_URL}")
    
    try:
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print(" Connected to Supabase")
        
        required_tables = ['sessions', 'results', 'agent_logs', 'scrape_cache']
        all_exist = True
        
        print("\nChecking tables:")
        for table in required_tables:
            try:
                # Try to query the table
                result = client.table(table).select("*").limit(1).execute()
                print(f"   {table} - exists")
            except Exception as e:
                print(f"   {table} - missing or error: {str(e)[:50]}")
                all_exist = False
        
        if all_exist:
            print("\n" + "=" * 60)
            print(" All tables exist!")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print(" Some tables are missing")
            print("=" * 60)
            print("\nTo create tables:")
            print("1. Go to: https://pxvnhzfysqmjzqbhtpgx.supabase.co")
            print("2. Click 'SQL Editor' in the left sidebar")
            print("3. Copy the contents of: backend/db/schema.sql")
            print("4. Paste and click 'Run'")
            print("\nOr run: python scripts/create_tables.py")
            return False
            
    except Exception as e:
        print(f"\n Connection error: {e}")
        return False

def test_insert():
    """Test inserting data into tables."""
    print("\n" + "=" * 60)
    print("Testing Database Operations")
    print("=" * 60)
    
    try:
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Test session insert
        print("\nTesting session insert...")
        session_data = {
            "query": "test query",
            "status": "complete"
        }
        result = client.table("sessions").insert(session_data).execute()
        session_id = result.data[0]['id']
        print(f" Session created: {session_id}")
        
        # Test result insert
        print("\nTesting result insert...")
        result_data = {
            "session_id": session_id,
            "rank": 1,
            "url": "https://example.com",
            "title": "Test Result",
            "description": "Test description",
            "content_snippet": "Test content",
            "domain": "example.com",
            "relevance_score": 0.95,
            "topic_cluster": "Test"
        }
        client.table("results").insert(result_data).execute()
        print(" Result inserted")
        
        # Test agent log insert
        print("\nTesting agent log insert...")
        log_data = {
            "session_id": session_id,
            "agent_name": "test",
            "event_type": "complete",
            "message": "Test log"
        }
        client.table("agent_logs").insert(log_data).execute()
        print(" Agent log inserted")
        
        # Clean up test data
        print("\nCleaning up test data...")
        client.table("sessions").delete().eq("id", session_id).execute()
        print(" Test data cleaned up")
        
        print("\n" + "=" * 60)
        print(" All database operations working!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n Database operation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    tables_ok = check_tables()
    
    if tables_ok:
        test_insert()
    else:
        print("\n  Fix table issues before testing operations")
