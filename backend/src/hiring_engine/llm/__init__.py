"""LLM package — auto-selects best available provider."""

from hiring_engine.llm.base import BaseLLMClient


def get_llm_client() -> BaseLLMClient:
    """Get the best available LLM client. Prefers Groq (fast + free), falls back to Gemini."""
    from hiring_engine.config import get_settings

    settings = get_settings()

    # Prefer Groq if key is available (fast, free, reliable)
    if settings.groq_api_key:
        from hiring_engine.llm.groq_client import GroqLLMClient
        return GroqLLMClient()

    # Fallback to Gemini
    if settings.gemini_api_key:
        from hiring_engine.llm.gemini_client import GeminiLLMClient
        return GeminiLLMClient()

    raise RuntimeError("No LLM API key configured. Set GROQ_API_KEY or GEMINI_API_KEY in .env")


__all__ = ["BaseLLMClient", "get_llm_client"]
