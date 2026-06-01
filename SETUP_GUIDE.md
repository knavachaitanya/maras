# MARAS Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 20+
- Supabase account (free tier works)
- OpenAI API key

## Step-by-Step Setup

### 1. Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` and fill in:

**Supabase Configuration:**
1. Go to [supabase.com](https://supabase.com)
2. Create a new project (or use existing)
3. Go to Settings → API
4. Copy:
   - Project URL → `SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_URL`
   - `service_role` key → `SUPABASE_SERVICE_KEY`
   - `anon` key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`

**OpenAI Configuration:**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create API key
3. Copy to `OPENAI_API_KEY`

### 2. Database Setup

1. Open your Supabase project
2. Go to SQL Editor
3. Copy the entire contents of `backend/db/schema.sql`
4. Paste and run in SQL Editor
5. Verify tables are created in Table Editor

### 3. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Test backend
python main.py
```

Backend should start at http://localhost:8000

### 4. Frontend Setup

```bash
# Navigate to frontend (from project root)
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend should start at http://localhost:3000

### 5. Start Both Servers (Recommended)

From project root:

```bash
# Install root dependencies
npm install

# Start both servers concurrently
npm run dev
```

This starts:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### 6. Generate Codebase Graph (Optional)

```bash
npm run graph
```

View at: http://localhost:3000/graph

## Testing the System

1. Open http://localhost:3000
2. Enter a search query (e.g., "latest AI news")
3. Watch the agent status bar as agents process the query
4. View ranked results

## Troubleshooting

### Backend won't start
- Check `.env` has correct Supabase and OpenAI keys
- Verify Python 3.11+ is installed: `python --version`
- Check port 8000 is not in use

### Frontend won't start
- Check Node.js 20+ is installed: `node --version`
- Delete `node_modules` and `.next`, then `npm install`
- Check port 3000 is not in use

### No results appearing
- Check backend logs for errors
- Verify Supabase tables were created correctly
- Check OpenAI API key has credits
- Test backend health: http://localhost:8000/health

### Playwright errors
- Run: `playwright install chromium`
- On Linux, may need: `playwright install-deps`

## Health Check

Run the health check script:

```bash
python scripts/health_check.py
```

## Docker Deployment

```bash
# Build and start all services
docker compose up --build

# Run in background
docker compose up -d

# Stop services
docker compose down
```

## Next Steps

- Customize agent instructions in `backend/agents/`
- Adjust ranking weights in `backend/services/ranker.py`
- Modify UI styling in `frontend/src/components/`
- Add more search engines in `backend/services/scraper.py`

## Support

For issues, check:
1. Backend logs
2. Browser console (F12)
3. Supabase logs (Dashboard → Logs)
4. OpenAI usage (platform.openai.com)
