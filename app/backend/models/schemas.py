"""
Pydantic models for API request/response schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ============ Request Models ============

class AnalyzeTextRequest(BaseModel):
    """Request to analyze resume from pasted text."""
    resume_text: str = Field(..., min_length=100, description="Resume text content")


class RefineRequest(BaseModel):
    """Request to refine job recommendations."""
    session_id: str = Field(..., description="Session ID from analyze response")
    feedback: str = Field(..., min_length=3, description="Refinement feedback")


# ============ Response Models ============

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str


class AnalysisResponse(BaseModel):
    """Response from resume analysis."""
    status: str
    session_id: str
    result: str  # Markdown formatted result
    processing_time_ms: int


class RefineResponse(BaseModel):
    """Response from refinement."""
    status: str
    session_id: str
    result: str  # Markdown formatted result
    processing_time_ms: int


class ErrorResponse(BaseModel):
    """Error response."""
    status: str = "error"
    detail: str
    code: Optional[str] = None
