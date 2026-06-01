#!/usr/bin/env python3
"""Check if Supabase database tables are set up correctly."""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from supabase import create_client
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print(" Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in .env")
        sys.exit(1)
    
    print(f" Connecting to Supabase: {SUPABASE_URL}")
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Check each table
    tables = ["sessions", "queries", "results", "agent_logs", "scrape_cache"]
    
    print("\n Checking database tables...\n")
    
    all_good = True
    for table in tables:
        try:
            # Try to query the table
            result = client.table(table).select("*").limit(1).execute()
            print(f" Table '{table}' exists and is accessible")
        except Exception as e:
            print(f" Table '{table}' - Error: {str(e)}")
            all_good = False
    
    print("\n" + "="*60)
    
    if all_good:
        print(" All database tables are set up correctly!")
        print("\nYou can now start the application:")
        print("1. Backend: cd backend && .venv\\Scripts\\activate && python main.py")
        print("2. Frontend: cd frontend && npm run dev")
    else:
        print(" Some tables are missing or inaccessible!")
        print("\n To fix this:")
        print("1. Go to your Supabase project dashboard")
        print("2. Click 'SQL Editor' in the left sidebar")
        print("3. Open backend/db/schema.sql in a text editor")
        print("4. Copy ALL the contents")
        print("5. Paste into Supabase SQL Editor")
        print("6. Click 'Run' (or press Ctrl+Enter)")
        print("7. Run this script again to verify")
    
    print("="*60)
    
except ImportError:
    print(" Error: supabase package not installed")
    print("\nTo fix:")
    print("cd backend")
    print(".venv\\Scripts\\activate")
    print("pip install supabase")
    sys.exit(1)
except Exception as e:
    print(f" Error: {str(e)}")
    sys.exit(1)
