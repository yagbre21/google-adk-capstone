# Agentic Job Search - Web App

Web interface for the Agentic Job Search Recommender.

## Architecture

```
app/
├── backend/                 # FastAPI (Python)
│   ├── api/routes/         # API endpoints
│   ├── core/               # Config, dependencies
│   ├── models/             # Pydantic schemas
│   ├── services/           # Business logic
│   │   ├── session_service.py
│   │   ├── resume_service.py
│   │   └── analysis_service.py
│   ├── pipeline.py         # ADK pipeline (from notebook)
│   └── main.py             # Entry point
│
├── frontend/               # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── hooks/          # Custom hooks (useAnalysis)
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript types
│   └── package.json
│
└── docker-compose.yml      # Local development
```

## Quick Start (Local)

### Option 1: Run directly

```bash
# Backend
cd backend
cp .env.example .env  # Add your GOOGLE_API_KEY
pip install -r requirements.txt
python main.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Option 2: Docker Compose

```bash
export GOOGLE_API_KEY=your_key_here
docker-compose up
```

### Option 3: Script

```bash
export GOOGLE_API_KEY=your_key_here
./run-local.sh
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/analyze` | Analyze resume (file or text) |
| POST | `/api/v1/refine` | Refine recommendations |

## Deploy to Cloud Run

```bash
# Build and push backend
cd backend
gcloud builds submit --tag gcr.io/PROJECT_ID/agentic-job-search-backend
gcloud run deploy agentic-job-search-backend \
  --image gcr.io/PROJECT_ID/agentic-job-search-backend \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY

# Build and push frontend
cd ../frontend
gcloud builds submit --tag gcr.io/PROJECT_ID/agentic-job-search-frontend
gcloud run deploy agentic-job-search-frontend \
  --image gcr.io/PROJECT_ID/agentic-job-search-frontend
```

## TODO

- [ ] Extract full pipeline from `agentic_job_search.ipynb` into `pipeline.py`
- [ ] Add Redis for session storage in production
- [ ] Add rate limiting
- [ ] Add streaming responses for real-time progress
