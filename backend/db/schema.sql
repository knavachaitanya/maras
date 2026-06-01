-- backend/db/schema.sql

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Sessions
create table sessions (
  id          uuid primary key default uuid_generate_v4(),
  created_at  timestamptz default now(),
  query       text not null,
  status      text default 'pending',  -- pending | running | complete | error
  user_ip     text
);

-- Queries log
create table queries (
  id          uuid primary key default uuid_generate_v4(),
  session_id  uuid references sessions(id) on delete cascade,
  query       text not null,
  created_at  timestamptz default now()
);

-- Scraped + ranked results
create table results (
  id               uuid primary key default uuid_generate_v4(),
  session_id       uuid references sessions(id) on delete cascade,
  rank             int not null,
  url              text not null,
  final_url        text,
  title            text,
  description      text,
  snippet          text,
  content_snippet  text,
  og_image         text,
  domain           text,
  source_domain    text,
  favicon_url      text,
  price            text,
  relevance_score  float,
  bm25_score       float,
  semantic_score   float,
  category         text,
  topic_cluster    text,
  is_verified      boolean default false,
  is_product_page  boolean default false,
  scraped_at       timestamptz,
  created_at       timestamptz default now()
);

-- Agent activity log
create table agent_logs (
  id          uuid primary key default uuid_generate_v4(),
  session_id  uuid,
  agent_name  text not null,
  event_type  text not null,   -- start | complete | handoff | cache_hit | error
  message     text,
  metadata    jsonb,
  created_at  timestamptz default now()
);

-- Scrape cache (avoid re-scraping same query within TTL)
create table scrape_cache (
  id          uuid primary key default uuid_generate_v4(),
  query_hash  text unique not null,
  query       text not null,
  results     jsonb not null,
  expires_at  timestamptz not null,
  created_at  timestamptz default now()
);

-- Row Level Security (enable for production)
alter table sessions      enable row level security;
alter table results       enable row level security;
alter table agent_logs    enable row level security;
alter table scrape_cache  enable row level security;

-- Policies (allow all for service_role key)
create policy "service_role_all" on sessions      for all using (true);
create policy "service_role_all" on results       for all using (true);
create policy "service_role_all" on agent_logs    for all using (true);
create policy "service_role_all" on scrape_cache  for all using (true);

-- Indexes for performance
create index idx_results_session    on results(session_id);
create index idx_results_rank       on results(session_id, rank);
create index idx_agent_logs_session on agent_logs(session_id, created_at);
create index idx_scrape_cache_hash  on scrape_cache(query_hash);
create index idx_scrape_expires     on scrape_cache(expires_at);
