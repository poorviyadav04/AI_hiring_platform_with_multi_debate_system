"""Application configuration using Pydantic Settings."""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM
    gemini_api_key: str = ""
    gemini_model_fast: str = "gemini-2.0-flash"
    gemini_model_smart: str = "gemini-2.5-flash-preview-04-17"

    # Groq (free fallback)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""

    # GitHub
    github_token: Optional[str] = None

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "*"

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
