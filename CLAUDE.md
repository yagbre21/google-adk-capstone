# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Agentic Job Search Recommender** - Multi-agent AI system that analyzes resumes and provides calibrated job recommendations across 4 tiers. Built for Kaggle Agents Intensive Capstone (Nov 2025).

Core insight: Job boards match keywords. This system creates artificial tension through agent deliberation—Conservative and Optimistic evaluators debate your level, reach consensus, then find jobs you'd actually take.

## Development Commands

```bash
# Backend
cd app/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add GOOGLE_API_KEY
python main.py        # http://localhost:8000

# Frontend (separate terminal)
cd app/frontend
npm install
npm run dev           # http://localhost:5173
npm run build         # TypeScript check + Vite build
npm run lint          # ESLint

# Docker (full stack)
cd app
export GOOGLE_API_KEY=your_key
docker-compose up                              # Production build
docker-compose up backend frontend-dev         # Dev with hot reload
```

API docs: `/api/docs` (Swagger), `/api/redoc`

## Architecture

### Agent Pipeline (`app/backend/pipeline.py`)

```
Resume → Parser → Classifier → [Conservative ⚔ Optimistic] → Consensus
                                           ↓
            [Exact ⚔ Level Up] then [Stretch ⚔ Trajectory] → Validator → Formatter
```

**Model Tiers** (configurable via `MODEL_CONFIGS`):
- `fast`: Gemini 2.5 Flash-Lite/Flash
- `standard`: Gemini 3 Flash across all agents
- `deep`: Gemini 3 Pro for consensus agent

**Agents:**
1. **Resume Parser** - Extracts skills, YOE, trajectory. Uses `calculate_yoe` tool.
2. **Level Classifier** - Research-grounded leveling (1-10 scale) for any profession.
3. **Conservative Evaluator** - Skeptical hiring manager (looks for gaps).
4. **Optimistic Evaluator** - Talent recruiter (looks for potential).
5. **Consensus Agent** - Weighted voting: 50% Most Likely, 25% Conservative, 25% Optimistic.
6-9. **Job Scouts** (4x parallel) - One per tier.
10. **URL Validator** - Validates Google Search URLs.
11. **Formatter** - Markdown output with compensation estimates.

### Key Files

| File | Purpose |
|------|---------|
| `app/backend/pipeline.py` | All ADK agents and orchestration |
| `app/backend/main.py` | FastAPI entry, lifespan handler |
| `app/backend/core/config.py` | Settings (pydantic-settings) |
| `app/backend/api/routes/analyze.py` | API endpoints |
| `app/frontend/src/App.tsx` | Main React app, state |
| `app/frontend/src/hooks/useAnalysis.ts` | SSE streaming hook |

### Custom Tools

- `calculate_yoe(resume_text)` - Date parsing with overlap deduplication
- `check_job_urls(job_output)` - URL validation (self-healing pattern)

### Rate Limiting

Job scouts run batched parallel (2+2) with `STAGGER_DELAY = 2.0s` to avoid Google Search API limits.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | From AI Studio |
| `DEBUG` | No | Enable debug mode |
| `CORS_ORIGINS` | No | Allowed origins (default: localhost:5173) |

## Cloud Run Deployment

```bash
cd app/backend
gcloud builds submit --tag gcr.io/PROJECT_ID/agentic-job-search-backend
gcloud run deploy agentic-job-search-backend \
  --image gcr.io/PROJECT_ID/agentic-job-search-backend \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY
```
