"""GitHub verification endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException

from hiring_engine.schemas.api_models import GitHubVerifyRequest
from hiring_engine.schemas.github import GitHubVerificationResult
from hiring_engine.github.verifier import GitHubVerifier
from api.dependencies import get_github_verifier

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/verify", response_model=GitHubVerificationResult)
async def verify_github(
    request: GitHubVerifyRequest,
    verifier: GitHubVerifier = Depends(get_github_verifier),
):
    """
    Verify a candidate's GitHub profile.

    Analyzes: account authenticity, commit patterns, skill verification,
    repo quality, and produces an overall trust score.
    """
    if not request.github_url:
        raise HTTPException(status_code=400, detail="GitHub URL is required")

    try:
        result = await verifier.verify(request.github_url, request.claimed_skills)
        if result is None:
            raise HTTPException(status_code=404, detail="GitHub profile not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("GitHub verification failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Verification failed. Please try again.")
