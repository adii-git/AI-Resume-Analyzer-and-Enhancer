@echo off
echo.
echo ⚡ ResumeIQ — ATS Resume Analyzer
echo ─────────────────────────────────
echo.

REM ── Backend ──────────────────────────────────────────────────────────────────
echo 📦 Setting up Python backend...
cd backend

IF NOT EXIST venv (
    python -m venv venv
)

call venv\Scripts\activate

pip install -q -r requirements.txt
python -m spacy download en_core_web_sm

IF NOT EXIST .env (
    copy .env.example .env
    echo ℹ️  Created .env — add your OPENAI_API_KEY for AI enhancement.
)

echo 🚀 Starting backend on http://localhost:8000...
start "ResumeIQ Backend" cmd /k "venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000"

cd ..

REM ── Frontend ─────────────────────────────────────────────────────────────────
echo.
echo 📦 Setting up React frontend...
cd frontend

IF NOT EXIST node_modules (
    npm install
)

echo 🌐 Starting frontend on http://localhost:3000...
start "ResumeIQ Frontend" cmd /k "npm start"

cd ..

echo.
echo ✅ Both services are starting!
echo    Frontend : http://localhost:3000
echo    Backend  : http://localhost:8000
echo    API Docs : http://localhost:8000/docs
echo.
pause
