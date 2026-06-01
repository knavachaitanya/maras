# MARAS Quick Start

## 🚀 Get Started in 5 Minutes

### 1. Prerequisites Check

```bash
# Check Python version (need 3.11+)
python --version

# Check Node version (need 20+)
node --version
```

### 2. Clone & Setup

```bash
# If using Git
git clone <your-repo> maras
cd maras

# Run setup script
# On Windows:
scripts\setup.bat

# On Mac/Linux:
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 3. Configure Environment

Edit `.env` file with your keys:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
OPENAI_API_KEY=sk-xxxxx
```

**Get Supabase Keys:**
- Go to supabase.com → Your Project → Settings → API
- Copy Project URL and both keys

**Get OpenAI Key:**
- Go to platform.openai.com → API Keys
- Create new key

### 4. Setup Database

1. Open Supabase Dashboard
2. Go to SQL Editor
3. Copy contents of `backend/db/schema.sql`
4. Paste and Execute

### 5. Start Application

```bash
# Start both frontend and backend
npm run dev
```

Visit:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### 6. Test It Out

1. Open http://localhost:3000
2. Enter a query: "latest AI developments"
3. Watch agents work in real-time
4. View ranked results

## 📁 Project Structure

```
maras/
├── backend/          # FastAPI + OpenSwarm agents
│   ├── agents/       # 5 specialized AI agents
│   ├── services/     # Scraping, ranking, database
│   ├── routers/      # API endpoints
│   └── swarm/        # Agent orchestration
├── frontend/         # Next.js 14 app
│   └── src/
│       ├── app/      # Pages (home, results, graph)
│       └── components/ # UI components
└── scripts/          # Setup and utility scripts
```

## 🔧 Common Commands

```bash
# Development
npm run dev              # Start both servers
npm run build            # Build frontend
npm run graph            # Generate codebase graph
npm run health           # Check service health

# Backend only
cd backend
python main.py           # Start backend

# Frontend only
cd frontend
npm run dev              # Start frontend
```

## 🐛 Troubleshooting

**Port already in use:**
```bash
# Change ports in .env
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

**Playwright errors:**
```bash
playwright install chromium
```

**Module not found:**
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

## 📚 Learn More

- Full documentation: See `mdfile.md`
- Detailed setup: See `SETUP_GUIDE.md`
- Architecture: See `mdfile.md` sections 2-5

## 🎯 What's Next?

- Customize agent behavior in `backend/agents/`
- Adjust UI styling in `frontend/src/components/`
- Add more data sources in `backend/services/scraper.py`
- Deploy with Docker: `docker compose up`

## 💡 Tips

- Use `npm run health` to verify all services
- Check backend logs for debugging
- View agent activity in real-time on results page
- Explore API docs at http://localhost:8000/docs

---

**Need help?** Check `SETUP_GUIDE.md` for detailed instructions.
