# Agent Pipeline Verification Checklist

Use this checklist to verify that the agent pipeline fix is working correctly.

## Pre-Flight Checks ✈️

### Environment Setup
- [ ] `.env` file exists in project root
- [ ] `SUPABASE_URL` is set in `.env`
- [ ] `SUPABASE_SERVICE_KEY` is set in `.env`
- [ ] `OPENAI_API_KEY` is set in `.env`
- [ ] `frontend/.env.local` exists
- [ ] `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`

### Database Setup
- [ ] Supabase project is created
- [ ] Database schema is applied (tables: sessions, results, agent_logs)
- [ ] Can connect to Supabase from backend

### Dependencies
- [ ] Backend dependencies installed: `cd backend && pip install -r requirements.txt`
- [ ] Frontend dependencies installed: `cd frontend && npm install`

## Backend Verification 🔧

### Start Backend
```bash
cd backend
python start.py
```

- [ ] Backend starts without errors
- [ ] Console shows: `INFO:     Uvicorn running on http://0.0.0.0:8000`
- [ ] No import errors
- [ ] No database connection errors

### Test Health Endpoint
```bash
curl http://localhost:8000/health
```

- [ ] Returns: `{"status":"ok"}`
- [ ] Response time < 1 second

### Test Search Endpoint
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test query","fast_mode":false}'
```

- [ ] Returns JSON with `session_id` and `status`
- [ ] `status` is `"started"`
- [ ] `session_id` is a valid UUID

### Check Backend Logs
After submitting a search, check the backend console:

- [ ] See: `[ORCHESTRATOR] Pipeline started for query: test query`
- [ ] See: `[RESEARCH] Starting web research...`
- [ ] See: `[RESEARCH] Fetched X results`
- [ ] See: `[ANALYSIS] Starting analysis...`
- [ ] See: `[ANALYSIS] Analysis complete - scored X results`
- [ ] See: `[QA] Starting validation...`
- [ ] See: `[QA] QA check passed - X valid results`
- [ ] See: `[UIFORMATTER] Starting UI formatting...`
- [ ] See: `[UIFORMATTER] Output formatted, length: X chars`
- [ ] See: `[ORCHESTRATOR] Pipeline complete! Returning X results`

## Frontend Verification 🎨

### Start Frontend
```bash
cd frontend
npm run dev
```

- [ ] Frontend starts without errors
- [ ] Console shows: `ready - started server on 0.0.0.0:3000`
- [ ] No TypeScript errors
- [ ] No build errors

### Open Browser
Navigate to: `http://localhost:3000`

- [ ] Page loads successfully
- [ ] See "MARAS" heading
- [ ] See search bar
- [ ] See "AI Agent Mode" subtitle

### Submit Search Query
Type: "best laptops under 75000" and click Search

- [ ] Search bar shows "Searching..."
- [ ] Redirects to `/results?session=...`
- [ ] See 5 agent status indicators
- [ ] See query displayed: "Results for 'best laptops under 75000'"

### Watch Agent Status Dots
Observe the 5 agent dots over 6-10 seconds:

- [ ] **Orchestrator**: Grey → Blue (pulsing) → Green
- [ ] **Research**: Grey → Blue (pulsing) → Green
- [ ] **Analysis**: Grey → Blue (pulsing) → Green
- [ ] **QA**: Grey → Blue (pulsing) → Green
- [ ] **UIFormatter**: Grey → Blue (pulsing) → Green

### Check Browser Console
Open DevTools (F12) and check Console tab:

- [ ] See: `[POLLING] Status: running, Results: 0`
- [ ] See: `[AGENT STATUS] Received X logs: ...`
- [ ] See: `[POLLING] Status: complete, Results: X`
- [ ] No errors in console
- [ ] No CORS errors
- [ ] No 404 errors

### Verify Results Display
After all agents complete:

- [ ] Results appear below agent status bar
- [ ] Each result shows:
  - [ ] Rank number
  - [ ] Title
  - [ ] Domain
  - [ ] Description
  - [ ] Favicon
  - [ ] Relevance score
  - [ ] Topic cluster
- [ ] Results are sorted by rank (1, 2, 3...)
- [ ] At least 3 results shown
- [ ] No "No results found" message

## Automated Test Verification 🤖

### Run Test Script
```bash
python test_agent_pipeline.py
```

- [ ] Test starts successfully
- [ ] See: `[1] Submitting search query...`
- [ ] See: `✅ Search submitted successfully`
- [ ] See: `[2] Polling for agent logs...`
- [ ] See polling progress with agent completions
- [ ] See: `✅ Pipeline completed!`
- [ ] See: `[3] Verifying agent logs...`
- [ ] All 5 agents show: `✅ AgentName: start, complete`
- [ ] See: `[4] Verifying final results...`
- [ ] See: `Result count: X` (where X > 0)
- [ ] See: `✅ Results found and formatted correctly!`
- [ ] See: `✅ ALL TESTS PASSED`

## Database Verification 💾

### Check Sessions Table
Query Supabase:
```sql
SELECT * FROM sessions ORDER BY created_at DESC LIMIT 5;
```

- [ ] Recent sessions exist
- [ ] `status` is `"complete"` for finished searches
- [ ] `query` matches submitted queries
- [ ] `created_at` timestamps are recent

### Check Results Table
Query Supabase:
```sql
SELECT session_id, COUNT(*) as result_count 
FROM results 
GROUP BY session_id 
ORDER BY MAX(created_at) DESC 
LIMIT 5;
```

- [ ] Results exist for recent sessions
- [ ] Each session has multiple results (typically 5-10)
- [ ] `rank` values are sequential (1, 2, 3...)

### Check Agent Logs Table
Query Supabase:
```sql
SELECT session_id, agent_name, event_type, message 
FROM agent_logs 
WHERE session_id = 'YOUR_SESSION_ID' 
ORDER BY created_at;
```

- [ ] Logs exist for all 5 agents
- [ ] Each agent has "start" and "complete" events
- [ ] Agent names match exactly: "Orchestrator", "Research", "Analysis", "QA", "UIFormatter"
- [ ] No "error" events (unless expected)
- [ ] Timestamps are in correct order

## Edge Case Testing 🧪

### Test 1: Empty Results
Submit query: "xyzabc123nonexistentquery"

- [ ] All agents complete successfully
- [ ] Status becomes "complete"
- [ ] Shows "No results found" message
- [ ] No errors in console

### Test 2: Cached Results
Submit the same query twice:

- [ ] First query: Takes 6-10 seconds
- [ ] Second query: Takes <1 second (cached)
- [ ] Both return same results
- [ ] Research agent logs "cache_hit"

### Test 3: Multiple Concurrent Searches
Submit 3 different queries quickly:

- [ ] All 3 get unique session IDs
- [ ] All 3 complete successfully
- [ ] No interference between sessions
- [ ] Results are correct for each query

### Test 4: Fast Mode
Submit query with fast_mode: true:

- [ ] Returns results immediately (no polling needed)
- [ ] Shows "⚡ Instant results from cache" banner
- [ ] No agent status bar shown
- [ ] Results display correctly

## Performance Verification ⚡

### Timing Checks
- [ ] Research agent: 2-4 seconds
- [ ] Analysis agent: <1 second
- [ ] QA agent: <1 second
- [ ] UIFormatter agent: <1 second
- [ ] Total pipeline: 5-10 seconds
- [ ] Frontend polling interval: 1 second
- [ ] Results appear within 10 seconds

### Resource Usage
- [ ] Backend CPU usage reasonable (<50% on average)
- [ ] Backend memory usage stable (no leaks)
- [ ] Frontend responsive during polling
- [ ] No browser tab freezing

## Error Handling Verification ❌

### Test Backend Crash
Stop backend while frontend is polling:

- [ ] Frontend shows error after timeout (30s)
- [ ] Error message displayed to user
- [ ] No infinite polling
- [ ] Can retry by submitting new query

### Test Database Disconnect
Temporarily break database connection:

- [ ] Backend logs error but doesn't crash
- [ ] Returns empty results gracefully
- [ ] Frontend shows "No results found"
- [ ] Can recover when database reconnects

### Test Invalid API Key
Set invalid OpenAI API key:

- [ ] Backend logs error
- [ ] Pipeline uses fallback scoring
- [ ] Results still returned (may be lower quality)
- [ ] No crash

## Final Checklist ✅

### Code Quality
- [ ] No console.log statements in production code (except debugging)
- [ ] No hardcoded values (use environment variables)
- [ ] Error handling in all async functions
- [ ] Type safety in TypeScript files

### Documentation
- [ ] `AGENT_PIPELINE_FIX.md` explains the fix
- [ ] `QUICK_FIX_SUMMARY.md` provides quick reference
- [ ] `AGENT_FLOW_DIAGRAM.md` shows visual flow
- [ ] `VERIFICATION_CHECKLIST.md` (this file) guides testing

### Deployment Ready
- [ ] All tests pass
- [ ] No errors in production build
- [ ] Environment variables documented
- [ ] Database schema applied
- [ ] CORS configured correctly

## Sign-Off 📝

Date: _______________

Tested by: _______________

### Results:
- [ ] All checks passed
- [ ] Some checks failed (document below)
- [ ] Ready for deployment
- [ ] Needs additional work

### Notes:
```
(Add any issues found or additional notes here)
```

---

## Quick Test Commands

```bash
# Test backend health
curl http://localhost:8000/health

# Test search endpoint
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test","fast_mode":false}'

# Run automated test
python test_agent_pipeline.py

# Check backend logs
cd backend && python start.py

# Check frontend
cd frontend && npm run dev
```

## Troubleshooting Quick Reference

| Issue | Check | Fix |
|-------|-------|-----|
| Grey dots | Backend logs | Verify agent names match |
| No results | Database connection | Check Supabase credentials |
| Timeout | OpenAI API | Verify API key is valid |
| CORS error | Frontend .env | Check NEXT_PUBLIC_API_URL |
| 404 errors | Backend running | Start backend on port 8000 |

---

**Last Updated:** After agent pipeline fix
**Version:** 1.0
**Status:** ✅ Ready for testing
