"""Dependency injection for FastAPI endpoints."""

import logging
from functools import lru_cache

from hiring_engine.config import get_settings
from hiring_engine.llm import get_llm_client, BaseLLMClient
from hiring_engine.scoring.skill_matcher import SkillMatcher
from hiring_engine.services.candidate_service import CandidateService
from hiring_engine.services.hiring_service import HiringService
from hiring_engine.github.verifier import GitHubVerifier

logger = logging.getLogger(__name__)

_llm_client = None
_skill_matcher = None
_candidate_service = None
_hiring_service = None
_github_verifier = None


def get_llm() -> BaseLLMClient:
    """Get singleton LLM client (auto-selects Groq or Gemini)."""
    global _llm_client
    if _llm_client is None:
        _llm_client = get_llm_client()
    return _llm_client


def get_skill_matcher() -> SkillMatcher:
    """Get singleton skill matcher (loads embedding model once)."""
    global _skill_matcher
    if _skill_matcher is None:
        _skill_matcher = SkillMatcher()
    return _skill_matcher


def get_candidate_service() -> CandidateService:
    """Get singleton candidate service."""
    global _candidate_service
    if _candidate_service is None:
        _candidate_service = CandidateService(
            llm=get_llm(), skill_matcher=get_skill_matcher()
        )
    return _candidate_service


def get_github_verifier() -> GitHubVerifier:
    """Get singleton GitHub verifier."""
    global _github_verifier
    if _github_verifier is None:
        _github_verifier = GitHubVerifier(llm=get_llm())
    return _github_verifier


def get_hiring_service() -> HiringService:
    """Get singleton hiring service."""
    global _hiring_service
    if _hiring_service is None:
        _hiring_service = HiringService(
            llm=get_llm(),
            github_verifier=get_github_verifier(),
        )
    return _hiring_service
