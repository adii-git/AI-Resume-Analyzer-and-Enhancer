#!/bin/bash
# ── ResumeIQ — One-command startup ────────────────────────────────────────────
set -e

echo ""
echo "⚡ ResumeIQ — ATS Resume Analyzer"
echo "────────────────────────────────"

# ── Backend ───────────────────────────────────────────────────────────────────
echo ""
echo "📦 Setting up Python backend..."
cd backend

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

source venv/bin/activate

pip install -q -r requirements.txt

# Download spaCy model if not already present
python3 -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null || \
  python3 -m spacy download en_core_web_sm

# Copy .env if not exists
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "ℹ️  Created .env — add your OPENAI_API_KEY there for AI enhancement."
fi

# Start FastAPI in background
echo "🚀 Starting backend on http://localhost:8000 ..."
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ..

# ── Frontend ──────────────────────────────────────────────────────────────────
echo ""
echo "📦 Setting up React frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
  npm install
fi

echo "🌐 Starting frontend on http://localhost:3000 ..."
npm start &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ Both services started!"
echo "   Frontend : http://localhost:3000"
echo "   Backend  : http://localhost:8000"
echo "   API Docs : http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both."

# Wait and cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
