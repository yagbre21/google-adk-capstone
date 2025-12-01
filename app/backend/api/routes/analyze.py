"""
Resume analysis API routes.
"""
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse

from core.config import get_settings

# Security: Maximum file size (10MB to match frontend)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_TEXT_LENGTH = 100_000  # 100k characters
from core.dependencies import get_resume_service, get_analysis_service
from models.schemas import (
    AnalyzeTextRequest,
    RefineRequest,
    AnalysisResponse,
    RefineResponse,
    HealthResponse,
    ErrorResponse
)
from services.resume_service import ResumeService, ResumeExtractionError
from services.analysis_service import AnalysisService, AnalysisError, StreamEvent

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.api_version
    )


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def analyze_resume(
    file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    resume_service: ResumeService = Depends(get_resume_service),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Analyze a resume and return job recommendations.

    Accepts either:
    - **file**: PDF or DOCX resume upload
    - **resume_text**: Plain text resume (pasted)

    Returns structured job recommendations across 4 tiers:
    - Exact Match: Jobs you could get now
    - Level Up: Your next promotion
    - Stretch: Ambitious but possible
    - Trajectory: Where your career is heading
    """
    try:
        # Extract text from file or use provided text
        if file and file.filename:
            file_bytes = await file.read()
            # Security: Validate file size
            if len(file_bytes) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size is {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
                )
            text = resume_service.extract_from_file(file_bytes, file.filename)
        elif resume_text:
            # Security: Validate text length
            if len(resume_text) > MAX_TEXT_LENGTH:
                raise HTTPException(
                    status_code=400,
                    detail=f"Text too long. Maximum length is {MAX_TEXT_LENGTH:,} characters."
                )
            text = resume_text
        else:
            raise HTTPException(
                status_code=400,
                detail="Please provide either a file upload or resume text."
            )

        # Validate the text
        text = resume_service.validate_text(text)

        # Run analysis
        session_id, result, processing_time = await analysis_service.analyze(text)

        return AnalysisResponse(
            status="success",
            session_id=session_id,
            result=result,
            processing_time_ms=processing_time
        )

    except ResumeExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AnalysisError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/refine",
    response_model=RefineResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def refine_results(
    request: RefineRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Refine job recommendations based on user feedback.

    Requires a valid session_id from a previous /analyze call.

    Example feedback:
    - "Remote only"
    - "Exclude crypto companies"
    - "Focus on startups"
    - "Higher compensation range"
    """
    try:
        result, processing_time = await analysis_service.refine(
            request.session_id,
            request.feedback
        )

        return RefineResponse(
            status="success",
            session_id=request.session_id,
            result=result,
            processing_time_ms=processing_time
        )

    except AnalysisError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/stream")
async def analyze_resume_stream(
    file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    model_mode: Optional[str] = Form("standard"),
    resume_service: ResumeService = Depends(get_resume_service),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Analyze a resume with real-time streaming progress updates.

    Uses Server-Sent Events (SSE) to stream agent progress to the client.

    Event types:
    - **progress**: Agent is working (includes agent name and preview)
    - **result**: Final result with session_id and processing time
    - **error**: Something went wrong

    Accepts either:
    - **file**: PDF or DOCX resume upload
    - **resume_text**: Plain text resume (pasted)
    - **model_mode**: "fast", "standard", or "deep" (default: "standard")
    """
    try:
        # Extract text from file or use provided text
        if file and file.filename:
            file_bytes = await file.read()
            # Security: Validate file size
            if len(file_bytes) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size is {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
                )
            text = resume_service.extract_from_file(file_bytes, file.filename)
        elif resume_text:
            # Security: Validate text length
            if len(resume_text) > MAX_TEXT_LENGTH:
                raise HTTPException(
                    status_code=400,
                    detail=f"Text too long. Maximum length is {MAX_TEXT_LENGTH:,} characters."
                )
            text = resume_text
        else:
            raise HTTPException(
                status_code=400,
                detail="Please provide either a file upload or resume text."
            )

        # Validate the text
        text = resume_service.validate_text(text)

        async def event_generator():
            async for event in analysis_service.analyze_stream(text, model_mode=model_mode):
                yield event.to_sse()

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    except ResumeExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refine/stream")
async def refine_results_stream(
    request: RefineRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Refine job recommendations with streaming progress updates.

    Uses Server-Sent Events (SSE) to stream agent progress.

    Requires a valid session_id from a previous /analyze call.
    """
    async def event_generator():
        async for event in analysis_service.refine_stream(
            request.session_id,
            request.feedback
        ):
            yield event.to_sse()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
