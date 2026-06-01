"""Automatically create Supabase database tables."""
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

# SQL to create tables
CREATE_TABLES_SQL = """
-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Sessions
create table if not exists sessions (
  id          uuid primary key default uuid_generate_v4(),
  created_at  timestamptz default now(),
  query       text not null,
  status      text default 'pending',
  user_ip     text
);

-- Results
create table if not exists results (
  id               uuid primary key default uuid_generate_v4(),
  session_id       uuid references sessions(id) on delete cascade,
  rank             int not null,
  url              text not null,
  final_url        text,
  title            text,
  description      text,
  content_snippet  text,
  og_image         text,
  domain           text,
  favicon_url      text,
  relevance_score  float,
  bm25_score       float,
  semantic_score   float,
  topic_cluster    text,
  is_product_page  boolean default false,
  scraped_at       timestamptz,
  created_at       timestamptz default now()
);

-- Agent logs
create table if not exists agent_logs (
  id          uuid primary key default uuid_generate_v4(),
  session_id  uuid,
  agent_name  text not null,
  event_type  text not null,
  message     text,
  metadata    jsonb,
  created_at  timestamptz default now()
);

-- Scrape cache
create table if not exists scrape_cache (
  id          uuid primary key default uuid_generate_v4(),
  query_hash  text unique not null,
  query       text not null,
  results     jsonb not null,
  expires_at  timestamptz not null,
  created_at  timestamptz default now()
);
"""

def create_tables():
    """Create database tables using Supabase REST API."""
    print("=" * 60)
    print("Creating Supabase Database Tables")
    print("=" * 60)
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print(" Missing Supabase credentials in .env file")
        return False
    
    print(f"\n Supabase URL: {SUPABASE_URL}")
    
    try:
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print(" Connected to Supabase")
        
        print("\n  Note: Table creation via Python client is limited.")
        print("For best results, use the Supabase SQL Editor:")
        print("\n1. Go to: https://pxvnhzfysqmjzqbhtpgx.supabase.co")
        print("2. Click 'SQL Editor' in the left sidebar")
        print("3. Copy the contents of: backend/db/schema.sql")
        print("4. Paste and click 'Run'")
        
        print("\n" + "=" * 60)
        print("Checking if tables already exist...")
        print("=" * 60)
        
        tables = ['sessions', 'results', 'agent_logs', 'scrape_cache']
        existing = []
        missing = []
        
        for table in tables:
            try:
                client.table(table).select("*").limit(1).execute()
                existing.append(table)
                print(f"   {table} - already exists")
            except:
                missing.append(table)
                print(f"   {table} - missing")
        
        if not missing:
            print("\n All tables already exist!")
            return True
        else:
            print(f"\n  Missing tables: {', '.join(missing)}")
            print("\nPlease create them using the Supabase SQL Editor (see instructions above)")
            return False
            
    except Exception as e:
        print(f"\n Error: {e}")
        return False

if __name__ == "__main__":
    create_tables()
