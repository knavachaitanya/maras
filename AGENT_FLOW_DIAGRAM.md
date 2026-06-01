# Agent Pipeline Flow Diagram

## Complete End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERACTION                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ User types query
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js/React)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. SearchBar.tsx                                                            │
│     └─> onSearch(query)                                                      │
│                                                                              │
│  2. page.tsx                                                                 │
│     └─> POST /api/search { query, fast_mode: false }                        │
│         ├─> Receives: { session_id, status: "started" }                     │
│         └─> Navigate to /results?session={session_id}                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP POST
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND (FastAPI)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  routers/search.py                                                           │
│  └─> @router.post("/search")                                                │
│      ├─> Generate session_id = uuid4()                                      │
│      ├─> Add background task: run_agent_pipeline(session_id, query)         │
│      └─> Return { session_id, status: "started" }                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Background Task
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AGENT PIPELINE (Async)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  swarm/runtime.py: run_agent_pipeline()                                     │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ ORCHESTRATOR                                                        │    │
│  │ ├─> Log: "Orchestrator:start"                                      │    │
│  │ ├─> Create session in database                                     │    │
│  │ └─> Initialize context = { session_id, query, results: [] }       │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              │ Handoff                                       │
│                              ▼                                               │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ RESEARCH AGENT                                                      │    │
│  │ ├─> Log: "Research:start"                                          │    │
│  │ ├─> Check cache for query                                          │    │
│  │ ├─> If not cached:                                                 │    │
│  │ │   ├─> Search web (Google, Bing, etc.)                           │    │
│  │ │   ├─> Scrape URLs (parallel)                                    │    │
│  │ │   └─> Cache results                                             │    │
│  │ ├─> Store in context["raw_results"]                               │    │
│  │ └─> Log: "Research:complete" (count: X)                           │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              │ Handoff                                       │
│                              ▼                                               │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ ANALYSIS AGENT                                                      │    │
│  │ ├─> Log: "Analysis:start"                                          │    │
│  │ ├─> Score results:                                                 │    │
│  │ │   ├─> BM25 keyword matching (40%)                               │    │
│  │ │   ├─> Semantic similarity (40%)                                 │    │
│  │ │   └─> Domain authority (20%)                                    │    │
│  │ ├─> Cluster by topic                                               │    │
│  │ ├─> Detect product pages                                           │    │
│  │ ├─> Store in context["scored_results"]                            │    │
│  │ └─> Log: "Analysis:complete" (count: X)                           │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              │ Handoff                                       │
│                              ▼                                               │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ QA AGENT                                                            │    │
│  │ ├─> Log: "QA:start"                                                │    │
│  │ ├─> Remove duplicates (URL + content hash)                         │    │
│  │ ├─> Filter low-relevance (< 0.10)                                  │    │
│  │ ├─> Validate required fields                                       │    │
│  │ ├─> Re-rank after deduplication                                    │    │
│  │ ├─> Store in context["validated_results"]                         │    │
│  │ └─> Log: "QA:complete" (valid: X, removed: Y)                     │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              │ Handoff                                       │
│                              ▼                                               │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ UIFORMATTER AGENT                                                   │    │
│  │ ├─> Log: "UIFormatter:start"                                       │    │
│  │ ├─> Format each result:                                            │    │
│  │ │   ├─> Add favicon URLs                                          │    │
│  │ │   ├─> Round relevance scores                                    │    │
│  │ │   ├─> Format timestamps                                         │    │
│  │ │   └─> Add UI metadata                                           │    │
│  │ ├─> Group by topic clusters                                        │    │
│  │ ├─> Save to database (sessions + results tables)                   │    │
│  │ ├─> Store in context["final_results"]                             │    │
│  │ └─> Log: "UIFormatter:complete" (count: X)                        │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              │ Complete                                      │
│                              ▼                                               │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ ORCHESTRATOR                                                        │    │
│  │ ├─> Update session status = "complete"                             │    │
│  │ ├─> Log: "Orchestrator:complete"                                   │    │
│  │ └─> Return results                                                 │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Data stored in Supabase
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATABASE (Supabase)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  sessions table:                                                             │
│  ├─> id: session_id                                                          │
│  ├─> query: "best laptops under 75000"                                      │
│  ├─> status: "complete"                                                      │
│  └─> created_at: timestamp                                                   │
│                                                                              │
│  results table:                                                              │
│  ├─> session_id: session_id                                                  │
│  ├─> rank: 1, 2, 3...                                                        │
│  ├─> url, title, description, etc.                                           │
│  └─> relevance_score, topic_cluster, etc.                                    │
│                                                                              │
│  agent_logs table:                                                           │
│  ├─> session_id: session_id                                                  │
│  ├─> agent_name: "Orchestrator", "Research", etc.                           │
│  ├─> event_type: "start", "complete", "error"                               │
│  ├─> message: "Fetched 10 results"                                           │
│  └─> created_at: timestamp                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Frontend polls every 1 second
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND POLLING                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  results/page.tsx                                                            │
│  └─> useEffect(() => {                                                       │
│      setInterval(() => {                                                     │
│        GET /api/results/{session_id}      // Get results                     │
│        GET /api/results/{session_id}/logs // Get agent logs                  │
│      }, 1000)                                                                │
│    })                                                                        │
│                                                                              │
│  AgentStatusBar.tsx                                                          │
│  └─> For each agent in ["Orchestrator", "Research", "Analysis", "QA",       │
│                          "UIFormatter"]:                                     │
│      ├─> Check logs for agent_name match                                    │
│      ├─> If "complete" event found → Green dot                              │
│      ├─> If "start" event found → Blue dot (pulsing)                        │
│      ├─> If "error" event found → Red dot                                   │
│      └─> Otherwise → Grey dot                                               │
│                                                                              │
│  ResultFeed.tsx                                                              │
│  └─> When status === "complete":                                            │
│      └─> Render results as cards                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ User sees results
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER SEES                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  ✅ Orchestrator  ✅ Research  ✅ Analysis  ✅ QA  ✅ UIFormatter            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🏆 Rank 1 - Dell Laptops                                            │   │
│  │ dell.com                                                             │   │
│  │ Shop Dell laptops with latest Intel processors...                   │   │
│  │ Relevance: 0.95 | Electronics                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🥈 Rank 2 - HP Laptops                                              │   │
│  │ hp.com                                                               │   │
│  │ Explore HP laptops perfect for work and gaming...                   │   │
│  │ Relevance: 0.92 | Electronics                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ... (more results)                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Timeline

```
Time    Event
────────────────────────────────────────────────────────────────────────
0.0s    User submits query
0.1s    POST /api/search → session_id returned
0.2s    Frontend starts polling
0.3s    Orchestrator starts
0.5s    Research agent starts
3.0s    Research agent completes (10 results)
3.1s    Analysis agent starts
3.8s    Analysis agent completes (10 scored)
3.9s    QA agent starts
4.5s    QA agent completes (8 valid)
4.6s    UIFormatter agent starts
5.2s    UIFormatter agent completes (8 formatted)
5.3s    Orchestrator completes
5.4s    Frontend receives complete status
5.5s    Results render on screen
```

## Agent Status Dot States

```
State       Color   Animation   Meaning
────────────────────────────────────────────────────────────────
pending     Grey    None        Agent hasn't started yet
running     Blue    Pulsing     Agent is currently executing
complete    Green   None        Agent finished successfully
error       Red     None        Agent encountered an error
```

## Database Flow

```
┌──────────────┐
│   sessions   │  Created when pipeline starts
│              │  Updated when pipeline completes
│  id          │  ← session_id (UUID)
│  query       │  ← User's search query
│  status      │  ← "pending" → "running" → "complete"
│  created_at  │  ← Timestamp
└──────────────┘
       │
       │ One-to-many
       ▼
┌──────────────┐
│   results    │  Created when UIFormatter completes
│              │
│  session_id  │  ← Links to sessions.id
│  rank        │  ← 1, 2, 3...
│  url         │  ← Result URL
│  title       │  ← Result title
│  description │  ← Result description
│  ...          │  ← More fields
└──────────────┘
       │
       │ Sibling table
       ▼
┌──────────────┐
│  agent_logs  │  Created throughout pipeline execution
│              │
│  session_id  │  ← Links to sessions.id
│  agent_name  │  ← "Orchestrator", "Research", etc.
│  event_type  │  ← "start", "complete", "error"
│  message     │  ← "Fetched 10 results"
│  created_at  │  ← Timestamp
└──────────────┘
```

## Key Points

1. **Agent names MUST match exactly** between backend logs and frontend expectations
2. **Polling happens every 1 second** to update agent status in real-time
3. **Background task** runs independently - frontend doesn't wait for it
4. **Database is the source of truth** - all state stored in Supabase
5. **Logs enable real-time UI updates** - frontend reads agent_logs table
6. **Pipeline is sequential** - each agent waits for previous to complete
7. **Graceful degradation** - if no results, pipeline completes with empty array

## Error Scenarios

```
Scenario                    Backend Behavior              Frontend Display
─────────────────────────────────────────────────────────────────────────────
No search results           Log warning, return []        "No results found"
Scraping fails              Log error, return []          "No results found"
Low relevance scores        QA filters them out           Fewer results shown
Database connection fails   Use in-memory fallback        Results still work
OpenAI API fails            Use fallback scoring          Results still work
Timeout (30s)               Pipeline continues            Frontend shows error
```
