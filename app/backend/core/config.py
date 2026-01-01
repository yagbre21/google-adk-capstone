"""
Application configuration using Pydantic Settings.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API
    app_name: str = "Agentic Job Search Recommender"
    debug: bool = False
    api_version: str = "v1"

    # Google AI - loaded from environment
    google_api_key: str = ""

    # CORS - comma-separated string, parsed to list (override with CORS_ORIGINS_STR env var)
    cors_origins_str: str = "http://localhost:5173,http://localhost:3000"

    # Rate limiting
    rate_limit_per_minute: int = 10

    # Session
    session_ttl_seconds: int = 3600  # 1 hour

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]

    model_config = {
        "env_file": ["../../.env", ".env"],  # Check root first, then local
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
