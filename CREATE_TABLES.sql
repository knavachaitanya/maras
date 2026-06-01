-- ============================================================
-- MARAS Database Tables
-- ============================================================
-- 
-- INSTRUCTIONS:
-- 1. Go to: https://pxvnhzfysqmjzqbhtpgx.supabase.co
-- 2. Click "SQL Editor" in the left sidebar
-- 3. Click "New Query"
-- 4. Copy this ENTIRE file
-- 5. Paste into the SQL editor
-- 6. Click "Run" (or press Ctrl+Enter)
-- 7. Wait for "Success. No rows returned"
-- 
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- Table 1: sessions
-- Stores search sessions
-- ============================================================
CREATE TABLE IF NOT EXISTS sessions (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  query       TEXT NOT NULL,
  status      TEXT DEFAULT 'pending',  -- pending | running | complete | error
  user_ip     TEXT
);

-- ============================================================
-- Table 2: results
-- Stores search results with rankings
-- ============================================================
CREATE TABLE IF NOT EXISTS results (
  id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id       UUID REFERENCES sessions(id) ON DELETE CASCADE,
  rank             INT NOT NULL,
  url              TEXT NOT NULL,
  final_url        TEXT,
  title            TEXT,
  description      TEXT,
  content_snippet  TEXT,
  og_image         TEXT,
  domain           TEXT,
  favicon_url      TEXT,
  relevance_score  FLOAT,
  bm25_score       FLOAT,
  semantic_score   FLOAT,
  topic_cluster    TEXT,
  is_product_page  BOOLEAN DEFAULT FALSE,
  scraped_at       TIMESTAMPTZ,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Table 3: agent_logs
-- Stores agent activity logs
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_logs (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id  UUID,
  agent_name  TEXT NOT NULL,
  event_type  TEXT NOT NULL,   -- start | complete | handoff | cache_hit | error
  message     TEXT,
  metadata    JSONB,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Table 4: scrape_cache
-- Caches scraped results to avoid re-scraping
-- ============================================================
CREATE TABLE IF NOT EXISTS scrape_cache (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  query_hash  TEXT UNIQUE NOT NULL,
  query       TEXT NOT NULL,
  results     JSONB NOT NULL,
  expires_at  TIMESTAMPTZ NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Indexes for Performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_results_session    ON results(session_id);
CREATE INDEX IF NOT EXISTS idx_results_rank       ON results(session_id, rank);
CREATE INDEX IF NOT EXISTS idx_agent_logs_session ON agent_logs(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_scrape_cache_hash  ON scrape_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_scrape_expires     ON scrape_cache(expires_at);

-- ============================================================
-- Row Level Security (RLS)
-- ============================================================
ALTER TABLE sessions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE results       ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs    ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_cache  ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Policies (Allow all for service_role key)
-- ============================================================
DROP POLICY IF EXISTS "service_role_all_sessions" ON sessions;
DROP POLICY IF EXISTS "service_role_all_results" ON results;
DROP POLICY IF EXISTS "service_role_all_agent_logs" ON agent_logs;
DROP POLICY IF EXISTS "service_role_all_scrape_cache" ON scrape_cache;

CREATE POLICY "service_role_all_sessions" 
  ON sessions FOR ALL 
  USING (true);

CREATE POLICY "service_role_all_results" 
  ON results FOR ALL 
  USING (true);

CREATE POLICY "service_role_all_agent_logs" 
  ON agent_logs FOR ALL 
  USING (true);

CREATE POLICY "service_role_all_scrape_cache" 
  ON scrape_cache FOR ALL 
  USING (true);

-- ============================================================
-- Done! 
-- ============================================================
-- 
-- You should see: "Success. No rows returned"
-- 
-- Next steps:
-- 1. Close this SQL editor
-- 2. Run: python scripts\setup_database.py (to verify)
-- 3. Restart your backend server
-- 4. Try searching!
-- 
-- ============================================================
