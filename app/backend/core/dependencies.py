"""
Dependency injection for FastAPI.
"""
from functools import lru_cache
from typing import Generator

from core.config import Settings, get_settings
from services.session_service import SessionService
from services.resume_service import ResumeService
from services.analysis_service import AnalysisService


# Singleton services
_session_service: SessionService | None = None
_resume_service: ResumeService | None = None
_analysis_service: AnalysisService | None = None


def get_session_service() -> SessionService:
    """Get or create SessionService singleton."""
    global _session_service
    if _session_service is None:
        _session_service = SessionService(ttl=get_settings().session_ttl_seconds)
    return _session_service


def get_resume_service() -> ResumeService:
    """Get or create ResumeService singleton."""
    global _resume_service
    if _resume_service is None:
        _resume_service = ResumeService()
    return _resume_service


def get_analysis_service() -> AnalysisService:
    """Get or create AnalysisService singleton."""
    global _analysis_service
    if _analysis_service is None:
        settings = get_settings()
        _analysis_service = AnalysisService(
            api_key=settings.google_api_key,
            session_service=get_session_service()
        )
    return _analysis_service
