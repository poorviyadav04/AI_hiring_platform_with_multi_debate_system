"""Hiring team endpoints."""

import logging
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException

from hiring_engine.schemas.api_models import HiringEvaluationResult
from hiring_engine.services.hiring_service import HiringService
from api.dependencies import get_hiring_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/evaluate", response_model=HiringEvaluationResult)
async def evaluate_candidates(
    resumes: List[UploadFile] = File(..., description="Resume PDF files (up to 20)"),
    job_description: str = Form(..., description="Job description text"),
    service: HiringService = Depends(get_hiring_service),
):
    """
    Evaluate multiple candidates against a job description.

    Upload up to 20 resume PDFs + job description to get:
    - Ranked candidate list with scores
    - Multi-agent debate per candidate
    - GitHub verification (if GitHub URL found in resume)
    - Key strengths and concerns per candidate
    """
    if len(resumes) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 resumes per batch")

    if len(job_description.strip()) < 50:
        raise HTTPException(status_code=400, detail="Job description too short (min 50 characters)")

    pdf_bytes_list = []
    for resume in resumes:
        if not resume.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files accepted. '{resume.filename}' is not a PDF.",
            )
        data = await resume.read()
        if len(data) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File '{resume.filename}' too large (max 10MB)",
            )
        pdf_bytes_list.append(data)

    try:
        result = await service.evaluate_candidates(pdf_bytes_list, job_description)
        return result
    except Exception as e:
        logger.error("Batch evaluation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Evaluation failed. Please try again.")
