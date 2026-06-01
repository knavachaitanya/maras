# MARAS Setup Checklist

Use this checklist to ensure everything is configured correctly.

## ☐ Prerequisites

- [ ] Python 3.11+ installed (`python --version`)
- [ ] Node.js 20+ installed (`node --version`)
- [ ] Git installed (optional, for version control)
- [ ] Text editor (VS Code, Sublime, etc.)
- [ ] Web browser (Chrome, Firefox, Edge)

## ☐ Accounts & API Keys

### Supabase
- [ ] Created Supabase account at supabase.com
- [ ] Created new project (or selected existing)
- [ ] Copied Project URL
- [ ] Copied `anon` (public) key
- [ ] Copied `service_role` (secret) key

### OpenAI
- [ ] Created OpenAI account at platform.openai.com
- [ ] Added payment method (required for API access)
- [ ] Created API key
- [ ] Verified API key has credits available

## ☐ Environment Configuration

- [ ] Copied `.env.example` to `.env`
- [ ] Filled in `SUPABASE_URL`
- [ ] Filled in `SUPABASE_SERVICE_KEY`
- [ ] Filled in `NEXT_PUBLIC_SUPABASE_URL`
- [ ] Filled in `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- [ ] Filled in `OPENAI_API_KEY`
- [ ] Verified no spaces or quotes around values
- [ ] Saved `.env` file

## ☐ Database Setup

- [ ] Opened Supabase project dashboard
- [ ] Navigated to SQL Editor
- [ ] Opened `backend/db/schema.sql` in text editor
- [ ] Copied entire contents
- [ ] Pasted into Supabase SQL Editor
- [ ] Clicked "Run" button
- [ ] Verified "Success. No rows returned" message
- [ ] Checked Table Editor shows 5 tables:
  - [ ] sessions
  - [ ] queries
  - [ ] results
  - [ ] agent_logs
  - [ ] scrape_cache

## ☐ Backend Setup

- [ ] Opened terminal/command prompt
- [ ] Navigated to `backend` directory
- [ ] Created virtual environment: `python -m venv .venv`
- [ ] Activated virtual environment:
  - Windows: `.venv\Scripts\activate`
  - Mac/Linux: `source .venv/bin/activate`
- [ ] Upgraded pip: `pip install --upgrade pip`
- [ ] Installed dependencies: `pip install -r requirements.txt`
- [ ] Installed Playwright: `playwright install chromium`
- [ ] Verified no error messages

## ☐ Frontend Setup

- [ ] Opened new terminal/command prompt
- [ ] Navigated to `frontend` directory
- [ ] Installed dependencies: `npm install`
- [ ] Verified no error messages
- [ ] Checked `node_modules` folder was created

## ☐ Root Setup

- [ ] Navigated to project root directory
- [ ] Installed root dependencies: `npm install`
- [ ] Verified `node_modules` folder created in root
- [ ] Verified `concurrently` package installed

## ☐ First Run

- [ ] From project root, ran: `npm run dev`
- [ ] Waited for both servers to start
- [ ] Verified backend message: "Uvicorn running on http://0.0.0.0:8000"
- [ ] Verified frontend message: "Local: http://localhost:3000"
- [ ] No error messages in terminal

## ☐ Backend Verification

- [ ] Opened browser to http://localhost:8000/health
- [ ] Saw: `{"status":"ok"}`
- [ ] Opened http://localhost:8000/docs
- [ ] Saw FastAPI Swagger documentation
- [ ] Verified endpoints listed:
  - [ ] POST /api/search
  - [ ] GET /api/results/{session_id}
  - [ ] GET /api/graph
  - [ ] GET /health

## ☐ Frontend Verification

- [ ] Opened browser to http://localhost:3000
- [ ] Saw MARAS landing page
- [ ] Saw search bar
- [ ] Saw "MARAS" title
- [ ] Saw "MultiAgent Research & Aggregation" subtitle
- [ ] No console errors (F12 → Console tab)

## ☐ Functionality Test

- [ ] Entered test query: "artificial intelligence"
- [ ] Clicked "Search" button
- [ ] Redirected to results page
- [ ] Saw agent status indicators:
  - [ ] Orchestrator
  - [ ] Research
  - [ ] Analysis
  - [ ] QA
  - [ ] UIFormatter
- [ ] Agents changed from pending → running → complete
- [ ] Results appeared after agents completed
- [ ] Results show:
  - [ ] Rank number
  - [ ] Favicon
  - [ ] Domain name
  - [ ] Title
  - [ ] Description
  - [ ] Relevance score bar
  - [ ] Topic cluster badge
- [ ] Clicked on a result
- [ ] Opened in new tab
- [ ] Went to correct website

## ☐ Optional: Graphify Setup

- [ ] From project root, ran: `npm run graph`
- [ ] Saw "Graph generated" message
- [ ] Verified `frontend/public/graph-data.json` created
- [ ] Opened http://localhost:3000/graph
- [ ] Saw codebase visualization (or "Graph data not available" if graphify not installed)

## ☐ Optional: Health Check

- [ ] Ran: `python scripts/health_check.py`
- [ ] Saw: "✅ Backend: OK"
- [ ] Saw: "✅ Frontend: OK"
- [ ] Saw: "✅ All services are healthy!"

## ☐ Optional: Test Data Seeding

- [ ] Activated backend venv
- [ ] Ran: `python scripts/seed_db.py`
- [ ] Saw: "✅ Seeded test data with session_id: ..."
- [ ] Opened provided URL in browser
- [ ] Saw test results displayed

## ☐ Troubleshooting (if needed)

### Backend won't start
- [ ] Checked `.env` file exists and has all keys
- [ ] Verified Python version is 3.11+
- [ ] Tried: `pip install -r requirements.txt` again
- [ ] Checked port 8000 not in use
- [ ] Looked at error message in terminal

### Frontend won't start
- [ ] Verified Node version is 20+
- [ ] Tried: `npm install` again
- [ ] Deleted `.next` folder and retried
- [ ] Checked port 3000 not in use
- [ ] Looked at error message in terminal

### No results appearing
- [ ] Checked backend terminal for errors
- [ ] Verified OpenAI API key is valid
- [ ] Checked OpenAI account has credits
- [ ] Verified Supabase tables exist
- [ ] Checked browser console (F12) for errors

### Playwright errors
- [ ] Ran: `playwright install chromium`
- [ ] On Linux: `playwright install-deps`
- [ ] Checked internet connection

## ☐ Production Deployment (Optional)

- [ ] Reviewed `SETUP_GUIDE.md` deployment section
- [ ] Configured production environment variables
- [ ] Set up domain and SSL certificate
- [ ] Tested Docker build: `docker compose build`
- [ ] Started containers: `docker compose up -d`
- [ ] Verified services running: `docker compose ps`
- [ ] Tested production URL
- [ ] Set up monitoring/logging

## ☐ Customization (Optional)

- [ ] Reviewed agent instructions in `backend/agents/`
- [ ] Adjusted ranking weights in `backend/services/ranker.py`
- [ ] Customized UI colors in `frontend/src/app/globals.css`
- [ ] Modified search engines in `backend/services/scraper.py`
- [ ] Added custom topic clusters in `backend/services/ranker.py`

## ✅ Completion

- [ ] All core features working
- [ ] Can search and get results
- [ ] Results are ranked and displayed correctly
- [ ] Agent status updates in real-time
- [ ] No critical errors in logs
- [ ] Ready for development/customization

---

## Quick Reference

**Start Development:**
```bash
npm run dev
```

**Stop Servers:**
- Press `Ctrl+C` in terminal

**Restart:**
- Stop servers
- Run `npm run dev` again

**Check Health:**
```bash
python scripts/health_check.py
```

**View Logs:**
- Backend: Terminal running backend
- Frontend: Terminal running frontend
- Browser: F12 → Console tab
- Supabase: Dashboard → Logs

**Common URLs:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Graph: http://localhost:3000/graph

---

**Need Help?**
- Check `START_HERE.md` for setup guide
- Review `SETUP_GUIDE.md` for detailed instructions
- See `ARCHITECTURE.md` for system overview
- Read `PROJECT_SUMMARY.md` for complete feature list

**Everything working?** 🎉
You're ready to start using MARAS!
