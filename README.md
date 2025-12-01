# Agentic Job Search Recommender

Your resume argues with itself. AI agents debate your level, reach consensus, then find jobs you'd actually take.

## Overview

Job boards treat your resume as a bag of keywords. They match "Python" to "Python" and call it a day. The real problem isn't search—it's calibration.

This multi-agent system creates artificial tension through deliberation:

```
Resume → Parser → Classifier → [Conservative ⚔ Optimistic] → Consensus
                                           ↓
            [Exact ⚔ Level Up] then [Stretch ⚔ Trajectory] → Validator → Output
```

**Seven stages. Three model tiers. Four job recommendations. One argument.**

## 4-Tier Job Output

| Tier | What It Means |
|------|---------------|
| Exact Match | You could land this next week |
| Level Up | Your next promotion, externally |
| Stretch | Ambitious but possible |
| Trajectory | Where your career wants to go |

## Tech Stack

**Backend:**
- Python 3.10+
- FastAPI + Uvicorn
- Google ADK (Agent Development Kit)
- Gemini 2.5 Flash, Pro, and Flash-Lite
- Google Search Grounding
- PyPDF2 + python-docx (document parsing)

**Frontend:**
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Server-Sent Events (SSE) for streaming

## ADK Concepts Demonstrated

Multi-agent orchestration, custom tools, built-in tools, A2A Protocol, Sessions, Memory, and Human-in-the-loop. The requirement was 3. This demonstrates 7.

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google API Key from [AI Studio](https://aistudio.google.com/apikey)

### Backend Setup

```bash
cd app/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Run the server
python main.py
```

Backend runs at `http://localhost:8000`

### Frontend Setup

```bash
cd app/frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs at `http://localhost:5173`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/analyze` | Analyze resume (non-streaming) |
| POST | `/api/v1/analyze/stream` | Analyze resume with SSE progress |
| POST | `/api/v1/refine` | Refine results with feedback |
| POST | `/api/v1/refine/stream` | Refine with SSE progress |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | API key for Gemini and Search Grounding |
| `DEBUG` | No | Enable debug mode (default: false) |
| `CORS_ORIGINS` | No | Allowed origins (default: localhost:5173) |

## Security Notes

- File uploads limited to 10MB
- Text input limited to 100,000 characters
- Resumes are not stored—processed in memory only
- API docs disabled in production (enable with DEBUG=true)
- CORS restricted to configured origins

## Competition

Built for the [Kaggle Agents Intensive Capstone Project](https://www.kaggle.com/competitions/agents-intensive-capstone-project) (November 2025).

**Track:** Concierge Agents

## Author

**Yves Agbre** — [LinkedIn](https://www.linkedin.com/in/yagbre/) · [GitHub](https://github.com/yagbre21)

## License

CC-BY-SA 4.0
