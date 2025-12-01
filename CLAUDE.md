# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Project Sugoi** is an AI-powered anime recommendation web app that uses conversational chat to deliver personalized anime suggestions. Built with React + FastAPI, it features multi-platform streaming integration and intelligent content filtering.

**Tech Stack:**
- Frontend: React 18 + Vite + Tailwind CSS (SPA architecture)
- Backend: FastAPI + Python 3.11 (async/await throughout)
- AI: Google Gemini (multi-model orchestration)
- Data: Firestore cache + AniList GraphQL + MyAnimeList + YouTube
- Deployment: Docker multi-stage build on Google Cloud Run

## Development Commands

### First-Time Setup
```bash
# Install all dependencies
npm run install:all

# Set up environment variables
cp .env.example .env
# Edit .env and add your actual API keys

# Create Python virtual environment (recommended)
cd backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cd ..
```

### Running Development Servers
```bash
# Terminal 1: Backend (FastAPI with auto-reload)
npm run dev:backend

# Terminal 2: Frontend (Vite dev server)
npm run dev:frontend

# Access: http://localhost:8080
```

### Building for Production
```bash
# Build frontend only
npm run build:frontend

# Docker build (multi-stage: frontend + backend)
docker build -t project-sugoi .
```

### Testing
```bash
# IMPORTANT: Always activate venv before running backend code
source backend/venv/bin/activate  # macOS/Linux

# Run tests
cd backend/tests
python3 -m pytest
```

## Architecture

### Backend Structure (FastAPI)

**Main Entry Point:** `backend/api.py`
- FastAPI app with session middleware
- Serves React SPA from `/static` in production
- All endpoints under `/api/*`
- OpenAPI spec auto-generated at `/api/docs`

**Key Endpoints:**
- `POST /api/chat` - Main recommendation engine
- `POST /api/verify-age` - Age verification
- `GET /api/trending` - Current season trending anime
- `POST /api/settings/save` - Save content preferences
- Lazy loading endpoints for metadata enrichment
- OP/ED theme discovery endpoints

**Services Layer** (`backend/services/`):
- `recommendation_router.py` - Compound AI router with 3-layer architecture
- `gemini_recommendations.py` - Gemini-specific recommendation logic
- `filtering.py` - Content filtering service
- `enrichment.py` - Metadata enrichment service
- `oped_discovery.py` - Opening/ending theme discovery
- `youtube_official.py` - YouTube official video verification

**Data Layer:**
- `firestore_cache.py` - Firestore MDM (Master Data Management) cache
  - Unified anime metadata from AniList, MAL, YouTube
  - Per-source expiry tracking
  - Title variant matching

### Frontend Structure (React SPA)

**Main Application:** `frontend/src/App.jsx`
- Single-file component architecture
- useState hooks for state management
- Manages: recommendations, conversation history, user settings

**Components:**
- `components/ChatApp.jsx` - Main chat interface
- `components/LandingPage.jsx` - Marketing landing page
- `components/ErrorBoundary.jsx` - React error boundary
- `components/OpedVideoPlayer.jsx` - YouTube embed component

### Recommendation Engine (Compound AI System)

**3-Layer Architecture:**
1. **Layer 0: Guard & Router (Classifier)**
   - Uses lightweight model for fast classification
   - Analyzes query difficulty, content safety, and required capabilities
   - Routes to appropriate worker based on RouterOutput schema

2. **Layer 1: Recommendation Workers**
   - **Easy Route:** Simple, direct queries
   - **Medium Route:** Standard recommendations
   - **Hard Route:** Complex queries needing deep reasoning
   - **Family Route:** Child-safe content filtering
   - **Mature Route:** Adult content with appropriate warnings

3. **Layer 2: Validator & Enricher**
   - Validates recommendations against user preferences
   - Enriches with metadata from multiple sources
   - Ensures content appropriateness and deduplication

**RouterOutput Schema:**
```python
difficulty: Literal["easy", "medium", "hard"]  # Query complexity
needs_grounding: bool  # Requires real-time data
content_mode: Literal["family", "mature", "general"]  # Content filtering
sanitized_query: str  # Cleaned user input
vibe_profile: str  # Extracted mood/preferences
```

### Data Flow Architecture

**Recommendation Pipeline:**
1. User query → `POST /api/chat`
2. Title detection (lightweight model)
3. If specific anime: Search AniList → Firestore cache
4. Generate recommendations (Gemini model)
5. Enrich metadata (parallel API calls to AniList, MAL, YouTube)
6. Filter by age/content settings
7. Deduplication (session-based)
8. Return anime cards + conversational message

**Lazy Loading Pattern:**
- Initial response: Basic metadata only
- User clicks "More Info": Frontend requests full metadata
- Reduces initial latency significantly

**OP/ED Theme Discovery Pipeline:**
1. User clicks theme button
2. Backend checks Firestore cache
3. If cache hit: Fetch fresh YouTube view count
4. If cache miss: Multi-source discovery (MAL, YouTube, Spotify, Apple Music)
5. Multi-layer quality filters and validation
6. Cache result with expiry tracking
7. Return enriched metadata with streaming links

**YouTube Official Video Validation:**
Multi-layer validation to ensure only official content:
- YouTube API verification
- Artist official channels
- Whitelist channels (major labels/platforms/studios)
- Topic channels
- Cross-platform validation (Spotify/Apple)

### Caching Strategy

**Firestore MDM Cache:**
- AniList data: 30-180 days (based on anime status)
- MAL ratings: 6 months
- YouTube trailers: 3 months
- OP/ED themes: 30 days

## Critical Implementation Details

### Environment Variables

**Frontend variables MUST use `VITE_PUBLIC_*` prefix:**
```bash
# Correct
VITE_PUBLIC_POSTHOG_KEY=your_key_here

# Wrong (won't be exposed to frontend)
VITE_POSTHOG_KEY=your_key_here
```

**Model Configuration:**
All Gemini model names should use environment variables for flexibility.

### Firestore Integration Pattern

Always use lazy initialization:
```python
db = None

def get_firestore_db():
    global db
    if db is None:
        db = firestore.Client(project="your-project", database="your-database")
    return db
```

### Docker Multi-Stage Build

**Stage 1:** Node.js frontend build
- Creates optimized production bundle

**Stage 2:** Python backend + static files
- Installs dependencies
- Copies frontend build from Stage 1
- Runs uvicorn

## Common Pitfalls to Avoid

**1. Backend Process Management:**
If you see connection errors, ensure no other process is using the port.

**2. YouTube Official Video Validation:**
- Never accept user uploads, AMVs, covers, or unofficial reuploads
- This validation is critical for DMCA compliance

**3. API Input Validation:**
- `anime_id` must be validated as integer
- `oped_type` must be whitelisted to "opening" or "ending" only

**4. YouTube API Quota Conservation:**
- YouTube Data API has daily quota limits
- Use single search query instead of multiple searches
- Gracefully handle `quotaExceeded` errors

## Test Organization

Backend tests are organized by category:
- `unit/` - Isolated unit tests
- `integration/` - Integration tests
- `filters/` - Content filtering tests
- `edge_cases/` - Edge case testing
- `security/` - Security-focused tests
- `smoke/` - Quick smoke tests

## Performance Characteristics

**Typical Response Time:** 3-5 seconds (with caching)

**Optimization Strategies:**
- Parallel API calls (`asyncio.gather()`)
- Aggressive caching
- Multi-model orchestration (lite for simple queries)
- Lazy metadata loading
