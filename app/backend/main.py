"""
FastAPI Application Entry Point
Agentic Job Search Recommender
"""
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core.config import get_settings
from core.dependencies import get_analysis_service
from api.routes.analyze import router as analyze_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Starting Agentic Job Search Recommender API...")
    settings = get_settings()

    if not settings.google_api_key:
        print("⚠️  Warning: GOOGLE_API_KEY not set. Pipeline will fail.")
    else:
        # Initialize the analysis service (loads ADK pipeline)
        try:
            analysis_service = get_analysis_service()
            await analysis_service.initialize()
            print("✅ ADK Pipeline initialized")
        except Exception as e:
            print(f"⚠️  Pipeline initialization failed: {e}")
            print("   API will attempt to initialize on first request")

    print(f"✅ API ready at http://localhost:8000")
    print(f"📚 Docs at http://localhost:8000/docs")

    yield

    # Shutdown
    print("👋 Shutting down...")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="""
        AI-powered resume analysis and job recommendations.

        Upload your resume or paste the text, and get personalized job recommendations
        across 4 tiers: Exact Match, Level Up, Stretch, and Trajectory.

        Built with Google ADK and Gemini.
        """,
        version=settings.api_version,
        lifespan=lifespan,
        # Only expose docs in debug mode
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None
    )

    # CORS - use configured origins only (no wildcard in production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["content-type", "authorization"],
    )

    # Routes
    app.include_router(analyze_router, prefix="/api/v1", tags=["Analysis"])

    # Serve static files (frontend build) in production
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(request: Request, full_path: str):
            """Serve SPA - return index.html for all non-API routes."""
            # Check if file exists in static dir
            file_path = static_dir / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            # Return index.html for SPA routing
            return FileResponse(static_dir / "index.html")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,  # Only reload in debug mode
        log_level="debug" if settings.debug else "info"
    )
