"""
Session management service.
In production, replace with Redis or Cloud Memorystore.
"""
import time
from typing import Optional, Any
from dataclasses import dataclass, field


@dataclass
class Session:
    """Session data container."""
    session_id: str
    resume_text: str
    last_result: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


class SessionService:
    """
    In-memory session management.

    TODO: For production, implement RedisSessionService with same interface.
    """

    def __init__(self, ttl: int = 3600):
        self._sessions: dict[str, Session] = {}
        self._ttl = ttl

    def create(self, session_id: str, resume_text: str) -> Session:
        """Create a new session."""
        session = Session(
            session_id=session_id,
            resume_text=resume_text
        )
        self._sessions[session_id] = session
        self._cleanup_expired()
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """Get session by ID, returns None if expired or not found."""
        session = self._sessions.get(session_id)
        if session is None:
            return None

        # Check expiration
        if time.time() - session.created_at > self._ttl:
            del self._sessions[session_id]
            return None

        return session

    def update(self, session_id: str, result: str, metadata: dict = None) -> Optional[Session]:
        """Update session with new result."""
        session = self.get(session_id)
        if session is None:
            return None

        session.last_result = result
        session.updated_at = time.time()
        if metadata:
            session.metadata.update(metadata)

        return session

    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def _cleanup_expired(self):
        """Remove expired sessions."""
        now = time.time()
        expired = [
            sid for sid, session in self._sessions.items()
            if now - session.created_at > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]
