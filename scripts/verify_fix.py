"""
Verification script to check if the database schema matches the code expectations.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.supabase_client import get_client
from config import settings

def verify_database():
    """Verify database tables and schema."""
    print(" Verifying database setup...")
    print(f" Supabase URL: {settings.SUPABASE_URL}")
    
    client = get_client()
    
    if not client:
        print(" Database client not initialized")
        print("   Make sure SUPABASE_URL and SUPABASE_SERVICE_KEY are set in .env")
        return False
    
    print(" Database client initialized")
    
    # Check if sessions table exists
    try:
        result = client.table("sessions").select("id").limit(1).execute()
        print(" 'sessions' table exists and is accessible")
    except Exception as e:
        print(f" Error accessing 'sessions' table: {e}")
        return False
    
    # Check if results table exists
    try:
        result = client.table("results").select("id").limit(1).execute()
        print(" 'results' table exists and is accessible")
    except Exception as e:
        print(f" Error accessing 'results' table: {e}")
        return False
    
    # Check if agent_logs table exists
    try:
        result = client.table("agent_logs").select("id").limit(1).execute()
        print(" 'agent_logs' table exists and is accessible")
    except Exception as e:
        print(f" Error accessing 'agent_logs' table: {e}")
        return False
    
    print("\n All required tables are present and accessible!")
    print("\n Summary:")
    print("   - sessions table: ")
    print("   - results table: ")
    print("   - agent_logs table: ")
    print("\n Database schema verification complete!")
    
    return True

if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
