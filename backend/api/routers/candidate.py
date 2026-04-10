"""Candidate-side endpoints — no auth required."""

import logging
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException

from hiring_engine.schemas.api_models import CandidateAnalysisResult
from hiring_engine.services.candidate_service import CandidateService
from api.dependencies import get_candidate_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=CandidateAnalysisResult)
async def analyze_candidate(
    resume: UploadFile = File(..., description="Resume PDF file"),
    job_description: str = Form(..., description="Job description text"),
    service: CandidateService = Depends(get_candidate_service),
):
    """
    Analyze a candidate's fit for a job.

    Upload a resume PDF and paste the job description to get:
    - Score card with component breakdown
    - Gap analysis (missing skills, experience, education)
    - Counterfactual scenarios (what would improve the score)
    - Personalized learning roadmap
    """
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await resume.read()
    if len(pdf_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    if len(job_description.strip()) < 50:
        raise HTTPException(status_code=400, detail="Job description too short (min 50 characters)")

    try:
        result = await service.analyze(pdf_bytes, job_description)
        return result
    except Exception as e:
        logger.error("Candidate analysis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")
