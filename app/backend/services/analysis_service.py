"""
Resume analysis service using ADK pipeline.
"""
import uuid
import time
import asyncio
import json
from typing import Optional, AsyncGenerator, Dict, Any
from dataclasses import dataclass

from services.session_service import SessionService


class AnalysisError(Exception):
    """Raised when analysis fails."""
    pass


@dataclass
class StreamEvent:
    """Represents a streaming progress event."""
    event_type: str  # "progress", "result", "error"
    agent_name: Optional[str] = None
    message: Optional[str] = None
    result: Optional[str] = None
    session_id: Optional[str] = None
    processing_time_ms: Optional[int] = None

    def to_sse(self) -> str:
        """Convert to Server-Sent Event format."""
        data = {
            "type": self.event_type,
            "agent": self.agent_name,
            "message": self.message,
            "result": self.result,
            "session_id": self.session_id,
            "processing_time_ms": self.processing_time_ms
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        return f"data: {json.dumps(data)}\n\n"


class AnalysisService:
    """
    Service for running the ADK resume analysis pipeline.

    This wraps the core ADK agents and provides a clean interface
    for the API layer.
    """

    def __init__(self, api_key: str, session_service: SessionService):
        self._api_key = api_key
        self._session_service = session_service
        self._pipeline_initialized = False

    async def initialize(self):
        """Initialize the ADK pipeline. Called on app startup."""
        if self._pipeline_initialized:
            return

        # Import and setup the pipeline
        # This will be extracted from the notebook
        from pipeline import setup_pipeline
        await setup_pipeline(self._api_key)
        self._pipeline_initialized = True

    def generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"session_{uuid.uuid4().hex[:8]}"

    async def analyze(self, resume_text: str) -> tuple[str, str, int]:
        """
        Analyze a resume and return job recommendations.

        Returns:
            tuple of (session_id, result_markdown, processing_time_ms)
        """
        if not self._pipeline_initialized:
            await self.initialize()

        session_id = self.generate_session_id()
        start_time = time.time()

        try:
            # Import the analysis function
            from pipeline import analyze_resume

            # Run the pipeline
            result = await analyze_resume(resume_text, session_id=session_id)

            # Store session for refinement
            session = self._session_service.create(session_id, resume_text)
            self._session_service.update(session_id, result)

            processing_time_ms = int((time.time() - start_time) * 1000)

            return session_id, result, processing_time_ms

        except Exception as e:
            raise AnalysisError(f"Pipeline execution failed: {str(e)}")

    async def refine(self, session_id: str, feedback: str) -> tuple[str, int]:
        """
        Refine job recommendations based on user feedback.

        Returns:
            tuple of (result_markdown, processing_time_ms)
        """
        if not self._pipeline_initialized:
            await self.initialize()

        # Validate session exists
        session = self._session_service.get(session_id)
        if session is None:
            raise AnalysisError("Session not found or expired. Please analyze a resume first.")

        start_time = time.time()

        try:
            from pipeline import refine_results

            result = await refine_results(feedback, session_id=session_id)

            # Update session
            self._session_service.update(session_id, result)

            processing_time_ms = int((time.time() - start_time) * 1000)

            return result, processing_time_ms

        except Exception as e:
            raise AnalysisError(f"Refinement failed: {str(e)}")

    async def analyze_stream(self, resume_text: str, model_mode: str = "standard") -> AsyncGenerator[StreamEvent, None]:
        """
        Analyze a resume with streaming progress updates.

        Args:
            resume_text: The resume text to analyze
            model_mode: "fast", "standard", or "deep" - controls model quality/speed

        Yields:
            StreamEvent objects for progress updates and final result
        """
        if not self._pipeline_initialized:
            await self.initialize()

        session_id = self.generate_session_id()
        start_time = time.time()

        # Queue to collect progress updates from callback
        progress_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

        # Callback to push progress to queue
        def progress_callback(agent_name: str, message: str):
            try:
                progress_queue.put_nowait((agent_name, message))
            except asyncio.QueueFull:
                pass

        # Yield initial progress with mode info
        mode_labels = {"fast": "Fast", "standard": "Standard", "deep": "Deep"}
        mode_label = mode_labels.get(model_mode, "Standard")
        yield StreamEvent(
            event_type="progress",
            agent_name="system",
            message=f"🚀 Starting agentic job search pipeline ({mode_label} mode)...",
            session_id=session_id
        )

        # Run pipeline in background task
        from pipeline import analyze_resume

        async def run_pipeline():
            return await analyze_resume(
                resume_text,
                session_id=session_id,
                progress_callback=progress_callback,
                model_mode=model_mode
            )

        # Start pipeline task
        pipeline_task = asyncio.create_task(run_pipeline())

        # Yield progress updates while pipeline runs
        while not pipeline_task.done():
            try:
                # Wait for progress with timeout
                agent_name, message = await asyncio.wait_for(
                    progress_queue.get(), timeout=0.1
                )
                yield StreamEvent(
                    event_type="progress",
                    agent_name=agent_name,
                    message=message
                )
            except asyncio.TimeoutError:
                continue
            except Exception:
                continue

        # Drain remaining progress events
        while not progress_queue.empty():
            try:
                agent_name, message = progress_queue.get_nowait()
                yield StreamEvent(
                    event_type="progress",
                    agent_name=agent_name,
                    message=message
                )
            except asyncio.QueueEmpty:
                break

        # Get result
        try:
            result = await pipeline_task

            # Store session for refinement
            session = self._session_service.create(session_id, resume_text)
            self._session_service.update(session_id, result)

            processing_time_ms = int((time.time() - start_time) * 1000)

            yield StreamEvent(
                event_type="result",
                result=result,
                session_id=session_id,
                processing_time_ms=processing_time_ms
            )

        except Exception as e:
            yield StreamEvent(
                event_type="error",
                message=f"Pipeline execution failed: {str(e)}"
            )

    async def refine_stream(self, session_id: str, feedback: str) -> AsyncGenerator[StreamEvent, None]:
        """
        Refine job recommendations with streaming progress updates.

        Yields:
            StreamEvent objects for progress updates and final result
        """
        if not self._pipeline_initialized:
            await self.initialize()

        # Validate session exists
        session = self._session_service.get(session_id)
        if session is None:
            yield StreamEvent(
                event_type="error",
                message="Session not found or expired. Please analyze a resume first."
            )
            return

        start_time = time.time()

        # Queue to collect progress updates from callback
        progress_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

        def progress_callback(agent_name: str, message: str):
            try:
                progress_queue.put_nowait((agent_name, message))
            except asyncio.QueueFull:
                pass

        yield StreamEvent(
            event_type="progress",
            agent_name="system",
            message=f"🔄 Refining results with feedback: {feedback[:50]}..."
        )

        from pipeline import refine_results

        async def run_refinement():
            return await refine_results(
                feedback,
                session_id=session_id,
                progress_callback=progress_callback
            )

        pipeline_task = asyncio.create_task(run_refinement())

        while not pipeline_task.done():
            try:
                agent_name, message = await asyncio.wait_for(
                    progress_queue.get(), timeout=0.1
                )
                yield StreamEvent(
                    event_type="progress",
                    agent_name=agent_name,
                    message=message
                )
            except asyncio.TimeoutError:
                continue
            except Exception:
                continue

        while not progress_queue.empty():
            try:
                agent_name, message = progress_queue.get_nowait()
                yield StreamEvent(
                    event_type="progress",
                    agent_name=agent_name,
                    message=message
                )
            except asyncio.QueueEmpty:
                break

        try:
            result = await pipeline_task
            self._session_service.update(session_id, result)
            processing_time_ms = int((time.time() - start_time) * 1000)

            yield StreamEvent(
                event_type="result",
                result=result,
                session_id=session_id,
                processing_time_ms=processing_time_ms
            )

        except Exception as e:
            yield StreamEvent(
                event_type="error",
                message=f"Refinement failed: {str(e)}"
            )
