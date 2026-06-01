# MARAS Architecture Diagram

## System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                     │
│                    (Web Browser)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP Request
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 14)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Pages:                                                   │   │
│  │  • / (Home/Search)                                       │   │
│  │  • /results (Results Display)                            │   │
│  │  • /graph (Codebase Visualization)                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Components:                                              │   │
│  │  • SearchBar → ResultFeed → ResultCard                   │   │
│  │  • AgentStatusBar (real-time updates)                    │   │
│  │  • GraphViewer (Graphify integration)                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ POST /api/search
                             │ GET /api/results/{id}
                             │ WS /ws/agent-stream
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Routers:                                             │   │
│  │  • /api/search    → Trigger agent pipeline               │   │
│  │  • /api/results   → Fetch results                        │   │
│  │  • /api/graph     → Codebase graph data                  │   │
│  │  • /ws/agent-stream → Real-time agent logs               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           OPENSWARM AGENT RUNTIME                         │   │
│  │                                                           │   │
│  │   ┌─────────────────────────────────────────────────┐    │   │
│  │   │  1. ORCHESTRATOR AGENT                          │    │   │
│  │   │     • Receives query                            │    │   │
│  │   │     • Decomposes into sub-tasks                 │    │   │
│  │   │     • Manages agent handoffs                    │    │   │
│  │   │     • Monitors progress                         │    │   │
│  │   └──────────────┬──────────────────────────────────┘    │   │
│  │                  │                                        │   │
│  │                  ├──► 2. RESEARCH AGENT                   │   │
│  │                  │      • Search engines (G/B/DDG)        │   │
│  │                  │      • Parallel URL scraping           │   │
│  │                  │      • Metadata extraction             │   │
│  │                  │      • Cache management                │   │
│  │                  │                                        │   │
│  │                  ├──► 3. ANALYSIS AGENT                   │   │
│  │                  │      • BM25 keyword scoring            │   │
│  │                  │      • Semantic embeddings             │   │
│  │                  │      • Topic clustering                │   │
│  │                  │      • Product detection               │   │
│  │                  │                                        │   │
│  │                  ├──► 4. QA AGENT                         │   │
│  │                  │      • Deduplication                   │   │
│  │                  │      • URL validation                  │   │
│  │                  │      • Quality filtering               │   │
│  │                  │      • Re-ranking                      │   │
│  │                  │                                        │   │
│  │                  └──► 5. UI FORMATTER AGENT               │   │
│  │                         • JSON formatting                 │   │
│  │                         • Metadata enrichment             │   │
│  │                         • Cluster grouping                │   │
│  │                         • Final payload                   │   │
│  │                                                           │   │
│  └───────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────────────────▼───────────────────────────────┐   │
│  │                    SERVICES                               │   │
│  │                                                           │   │
│  │  • scraper.py      → Playwright + BeautifulSoup4         │   │
│  │  • ranker.py       → BM25 + OpenAI Embeddings            │   │
│  │  • supabase_client → Database operations                 │   │
│  │  • graphify_service → Codebase visualization             │   │
│  └───────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Database Queries
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SUPABASE (PostgreSQL)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Tables:                                                  │   │
│  │  • sessions       → Search sessions                      │   │
│  │  • queries        → Query history                        │   │
│  │  • results        → Ranked results                       │   │
│  │  • agent_logs     → Agent activity                       │   │
│  │  • scrape_cache   → Cached scrapes (30min TTL)           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ External APIs
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│  • OpenAI API        → Embeddings (text-embedding-3-small)      │
│  • Google Search     → Search results                           │
│  • Bing Search       → Search results                           │
│  • DuckDuckGo        → Search results                           │
│  • Target Websites   → Content scraping                         │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Communication Flow

```
User Query: "latest AI developments"
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR                                               │
│ • Receives: "latest AI developments"                       │
│ • Creates: session_id                                      │
│ • Decomposes into sub-tasks                                │
│ • Dispatches to Research Agent                             │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ RESEARCH AGENT                                             │
│ • Searches: Google, Bing, DuckDuckGo                       │
│ • Scrapes: Top 20 URLs in parallel                         │
│ • Extracts: title, description, content, images            │
│ • Returns: raw_results[] (20 items)                        │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ ANALYSIS AGENT                                             │
│ • Receives: raw_results[]                                  │
│ • Scores: BM25 (40%) + Embeddings (40%) + Authority (20%) │
│ • Clusters: News, Technical, Product, etc.                 │
│ • Detects: Product pages                                   │
│ • Returns: scored_results[] (sorted by relevance)          │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ QA AGENT                                                   │
│ • Receives: scored_results[]                               │
│ • Removes: Duplicates (URL + content)                      │
│ • Filters: relevance_score < 0.15                          │
│ • Validates: URL reachability                              │
│ • Caps: 30 results max                                     │
│ • Returns: validated_results[] (clean, ranked)             │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ UI FORMATTER AGENT                                         │
│ • Receives: validated_results[]                            │
│ • Formats: JSON with all metadata                          │
│ • Enriches: favicons, display domains                      │
│ • Groups: By topic clusters                                │
│ • Saves: To Supabase results table                         │
│ • Returns: final_results{} (ready for frontend)            │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
                  Frontend
              (Display Results)
```

## Data Flow Through Context Variables

```python
context_variables = {
    "session_id": "uuid-1234",
    "query": "latest AI developments",
    
    # After Orchestrator
    "sub_tasks": [
        "search AI news",
        "find AI research papers",
        "locate AI product launches"
    ],
    
    # After Research Agent
    "raw_results": [
        {
            "url": "https://example.com/ai-news",
            "title": "Latest AI Developments",
            "description": "...",
            "content_snippet": "...",
            "source_domain": "example.com",
            "og_image": "https://...",
            "scraped_at": "2024-01-01T12:00:00Z"
        },
        # ... 19 more
    ],
    
    # After Analysis Agent
    "scored_results": [
        {
            # ... all raw_result fields +
            "relevance_score": 0.95,
            "rank": 1,
            "bm25_score": 0.92,
            "semantic_score": 0.88,
            "topic_cluster": "News",
            "is_product_page": false
        },
        # ... sorted by relevance
    ],
    
    # After QA Agent
    "validated_results": [
        {
            # ... all scored_result fields +
            "final_url": "https://example.com/ai-news",  # after redirect
            "rank": 1  # re-ranked after dedup
        },
        # ... max 30 items
    ],
    
    # After UI Formatter
    "final_results": {
        "session_id": "uuid-1234",
        "query": "latest AI developments",
        "total": 25,
        "results": [...],  # formatted for UI
        "clusters": {
            "News": [...],
            "Technical": [...],
            "Product": [...]
        },
        "generated_at": "2024-01-01T12:00:05Z"
    }
}
```

## Ranking Algorithm

```
For each result:

1. BM25 Score (keyword matching)
   ├─ Tokenize: query + (title + description + content)
   ├─ Calculate: BM25 relevance
   └─ Normalize: 0.0 - 1.0

2. Semantic Score (meaning similarity)
   ├─ Embed: query → vector
   ├─ Embed: (title + description + content) → vector
   ├─ Calculate: cosine_similarity(query_vec, doc_vec)
   └─ Normalize: 0.0 - 1.0

3. Authority Score (domain trust)
   ├─ Check: domain in authority list
   ├─ Assign: 0.5 (default) or 0.8 (authority)
   └─ Normalize: 0.0 - 1.0

4. Final Score
   └─ 0.4 × bm25 + 0.4 × semantic + 0.2 × authority

5. Sort by final_score (descending)

6. Assign rank: 1, 2, 3, ...
```

## Caching Strategy

```
Query: "AI news"
   │
   ▼
┌─────────────────────────────────┐
│ Check scrape_cache              │
│ • Hash query → MD5              │
│ • Lookup by hash                │
│ • Check expires_at > now        │
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    │         │
  MISS       HIT
    │         │
    ▼         ▼
┌─────┐   ┌──────────────────┐
│Scrape│   │Return cached     │
│Web   │   │results (instant) │
└──┬──┘   └──────────────────┘
   │
   ▼
┌─────────────────────────────────┐
│ Cache results                   │
│ • Store with 30min TTL          │
│ • Next identical query = instant│
└─────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DOCKER HOST                          │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Container: maras-frontend                       │  │
│  │  • Next.js production build                      │  │
│  │  • Port: 3000                                    │  │
│  │  • Env: NEXT_PUBLIC_API_URL                      │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
│                         │ HTTP                          │
│                         ▼                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Container: maras-backend                        │  │
│  │  • FastAPI + Uvicorn                             │  │
│  │  • Port: 8000                                    │  │
│  │  • Env: SUPABASE_*, OPENAI_API_KEY               │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
└─────────────────────────┼───────────────────────────────┘
                          │
                          │ HTTPS
                          ▼
                  ┌───────────────┐
                  │   SUPABASE    │
                  │  (Cloud SaaS) │
                  └───────────────┘
```

## File Organization Logic

```
backend/
├── main.py              → FastAPI app + CORS + routers
├── config.py            → Environment variables
│
├── agents/              → 5 AI agents (OpenSwarm)
│   ├── orchestrator.py  → Coordinates workflow
│   ├── research.py      → Web scraping
│   ├── analysis.py      → Ranking & clustering
│   ├── qa.py            → Validation & dedup
│   └── ui_formatter.py  → Output formatting
│
├── swarm/               → Agent runtime
│   ├── runtime.py       → Pipeline execution
│   └── protocols.py     → Message schemas
│
├── services/            → Business logic
│   ├── scraper.py       → Playwright + BS4
│   ├── ranker.py        → BM25 + embeddings
│   ├── supabase_client.py → DB operations
│   └── graphify_service.py → Graph data
│
├── routers/             → API endpoints
│   ├── search.py        → POST /api/search
│   ├── results.py       → GET /api/results
│   ├── graph.py         → GET /api/graph
│   └── ws.py            → WebSocket
│
└── db/                  → Database
    └── schema.sql       → Supabase schema

frontend/
└── src/
    ├── app/             → Next.js pages
    │   ├── page.tsx     → Home (search)
    │   ├── results/     → Results display
    │   └── graph/       → Codebase graph
    │
    ├── components/      → React components
    │   ├── SearchBar.tsx
    │   ├── ResultCard.tsx
    │   ├── ResultFeed.tsx
    │   ├── AgentStatusBar.tsx
    │   └── GraphViewer.tsx
    │
    ├── lib/             → Utilities
    │   ├── api.ts       → Backend client
    │   └── supabase.ts  → DB client
    │
    └── store/           → State
        └── searchStore.ts → Zustand
```

## Technology Choices Rationale

| Choice | Reason |
|--------|--------|
| **FastAPI** | Async support, auto OpenAPI docs, type hints |
| **Next.js 14** | App Router, SSR, React Server Components |
| **OpenSwarm** | Multi-agent orchestration, handoffs, context |
| **Supabase** | PostgreSQL + realtime + auth + free tier |
| **Playwright** | JavaScript rendering, reliable scraping |
| **BM25** | Fast keyword matching, no ML required |
| **OpenAI Embeddings** | Semantic understanding, high quality |
| **Tailwind CSS** | Rapid UI development, consistent design |
| **Zustand** | Lightweight state, no boilerplate |
| **Docker Compose** | Simple multi-container deployment |

---

This architecture provides:
- ✅ Scalability (async, parallel, caching)
- ✅ Reliability (error handling, validation, retries)
- ✅ Maintainability (clear separation, typed code)
- ✅ Performance (caching, indexes, parallel execution)
- ✅ Extensibility (modular agents, pluggable services)
