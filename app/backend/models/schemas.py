"""
Pydantic models for API request/response schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ============ Request Models ============

class AnalyzeTextRequest(BaseModel):
    """Request to analyze resume from pasted text."""
    resume_text: str = Field(
        ...,
        min_length=100,
        description="Resume text content (minimum 100 characters)",
        json_schema_extra={
            "example": "John Doe\nSenior Software Engineer at Google (2020-Present)\n- Led team of 5 engineers building ML infrastructure\n- 8 years experience in Python, Go, and distributed systems..."
        }
    )


class RefineRequest(BaseModel):
    """Request to refine job recommendations based on user feedback."""
    session_id: str = Field(
        ...,
        description="Session ID from a previous /analyze response",
        json_schema_extra={"example": "sess_abc123def456"}
    )
    feedback: str = Field(
        ...,
        min_length=3,
        description="Natural language feedback to refine results",
        json_schema_extra={"example": "Remote only, exclude crypto companies, focus on AI/ML roles"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "sess_abc123def456",
                "feedback": "Remote only, exclude crypto companies"
            }
        }
    )


# ============ Response Models ============

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    timestamp: datetime
    version: str = Field(..., json_schema_extra={"example": "v1"})


class AnalysisResponse(BaseModel):
    """Response from resume analysis with 4-tier job recommendations."""
    status: str = Field(..., json_schema_extra={"example": "success"})
    session_id: str = Field(
        ...,
        description="Use this ID for subsequent /refine calls",
        json_schema_extra={"example": "sess_abc123def456"}
    )
    result: str = Field(
        ...,
        description="Markdown-formatted analysis with job recommendations",
        json_schema_extra={"example": "## 📄 RESUME ANALYSIS\n\n**Current Role:** Senior Engineer at Google...\n\n## 🎯 EXACT MATCH: Staff Engineer, Stripe\n..."}
    )
    processing_time_ms: int = Field(
        ...,
        description="Total processing time in milliseconds",
        json_schema_extra={"example": 45000}
    )


class RefineResponse(BaseModel):
    """Response from refinement with updated job recommendations."""
    status: str = Field(..., json_schema_extra={"example": "success"})
    session_id: str = Field(..., json_schema_extra={"example": "sess_abc123def456"})
    result: str = Field(
        ...,
        description="Markdown-formatted refined recommendations",
        json_schema_extra={"example": "## 🔄 REFINED RECOMMENDATIONS\n\nBased on your feedback (remote only)...\n\n## 🎯 EXACT MATCH: Staff Engineer, GitLab (Remote)\n..."}
    )
    processing_time_ms: int = Field(..., json_schema_extra={"example": 30000})


class ErrorResponse(BaseModel):
    """Error response with details."""
    status: str = Field(default="error", json_schema_extra={"example": "error"})
    detail: str = Field(
        ...,
        description="Human-readable error message",
        json_schema_extra={"example": "File too large. Maximum size is 10MB."}
    )
    code: Optional[str] = Field(
        default=None,
        description="Error code for programmatic handling",
        json_schema_extra={"example": "FILE_TOO_LARGE"}
    )
