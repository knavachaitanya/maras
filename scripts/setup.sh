#!/usr/bin/env bash
set -e

echo "── MARAS Setup ──────────────────────────────────────────"

# 1. Copy .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✔ Created .env — fill in your Supabase and OpenAI keys"
fi

# 2. Python venv
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
echo "✔ Python dependencies installed"
cd ..

# 3. Node dependencies
npm install
cd frontend && npm install && cd ..
echo "✔ Node dependencies installed"

# 4. Run DB schema
echo "── Supabase Schema ─────────────────────────────────────"
echo "Open your Supabase project → SQL Editor → paste contents of backend/db/schema.sql → Run"
echo "Then press Enter to continue..."
read -r

# 5. Generate graphify graph
npm run graph
echo "✔ Graphify graph generated → frontend/public/graph-data.json"

echo ""
echo "✅ Setup complete! Run: npm run dev"
