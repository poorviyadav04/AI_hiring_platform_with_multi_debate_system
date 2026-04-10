"""Hiring team service — orchestrates bulk evaluation with GitHub verification."""

import asyncio
import logging
from typing import List, Optional, Dict, Any

from hiring_engine.llm.base import BaseLLMClient
from hiring_engine.parsers.resume_parser import parse_resume
from hiring_engine.parsers.jd_parser import parse_job_description
from hiring_engine.agents.workflow import MultiAgentWorkflow
from hiring_engine.github.verifier import GitHubVerifier
from hiring_engine.schemas.candidate import CandidateProfile
from hiring_engine.schemas.job import JobRequirements
from hiring_engine.schemas.constraints import HiringConstraints
from hiring_engine.schemas.api_models import (
    CandidateEvaluation,
    HiringEvaluationResult,
)

logger = logging.getLogger(__name__)


class HiringService:
    """Orchestrates hiring team evaluation flow."""

    def __init__(
        self,
        llm: BaseLLMClient,
        github_verifier: Optional[GitHubVerifier] = None,
    ):
        self._llm = llm
        self._github_verifier = github_verifier
        self._constraints = HiringConstraints(
            policy_id="POL-DEFAULT", policy_name="Standard Hiring Policy"
        )
        self._workflow = MultiAgentWorkflow(constraints=self._constraints, llm=llm)

    async def evaluate_candidates(
        self,
        resume_pdfs: List[bytes],
        jd_text: str,
    ) -> HiringEvaluationResult:
        """Evaluate multiple candidates against a job description."""
        logger.info("Starting batch evaluation: %d resumes", len(resume_pdfs))

        # Step 1: Parse JD
        jd_result = await parse_job_description(jd_text, self._llm)
        job = jd_result.job_requirements
        logger.info("Parsed JD: %s (%s)", job.title, job.level)

        # Step 2: Parse all resumes (parallel)
        parse_tasks = [parse_resume(pdf, self._llm) for pdf in resume_pdfs]
        resume_results = await asyncio.gather(*parse_tasks, return_exceptions=True)

        candidates = []
        for i, result in enumerate(resume_results):
            if isinstance(result, Exception):
                logger.error("Failed to parse resume %d: %s", i, result)
                continue
            candidates.append(result)

        logger.info("Successfully parsed %d/%d resumes", len(candidates), len(resume_pdfs))

        # Step 3: Evaluate each candidate (sequential to respect LLM rate limits)
        evaluations: List[CandidateEvaluation] = []
        for resume_result in candidates:
            candidate = resume_result.candidate_profile
            try:
                eval_result = await self._evaluate_single(candidate, job, resume_result.github_url)
                evaluations.append(eval_result)
            except Exception as e:
                logger.error("Failed to evaluate %s: %s", candidate.name, e)

        # Step 4: Sort by overall score (descending)
        evaluations.sort(key=lambda e: e.overall_score, reverse=True)

        import uuid
        evaluation_id = f"BATCH-{uuid.uuid4().hex[:8].upper()}"

        return HiringEvaluationResult(
            job_title=job.title,
            job_id=job.job_id,
            total_candidates=len(evaluations),
            rankings=evaluations,
            evaluation_id=evaluation_id,
        )

    async def _evaluate_single(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        github_url: Optional[str] = None,
    ) -> CandidateEvaluation:
        """Evaluate a single candidate with optional GitHub verification."""
        logger.info("Evaluating: %s", candidate.name)

        # Run multi-agent workflow
        result = await self._workflow.run(candidate, job)

        # GitHub verification (if URL available)
        github_verification = None
        if github_url and self._github_verifier:
            try:
                github_verification = await self._github_verifier.verify(
                    github_url, candidate.skills[:10]
                )
                logger.info(
                    "GitHub verified: %s trust=%.0f",
                    candidate.name,
                    github_verification.overall_trust_score if github_verification else 0,
                )
            except Exception as e:
                logger.warning("GitHub verification failed for %s: %s", candidate.name, e)

        # Extract strengths and concerns from debate
        strengths = []
        concerns = []
        for msg in result["debate_transcript"]:
            if msg["role"] == "advocate":
                strengths = _extract_bullet_points(msg["content"], limit=3)
            elif msg["role"] == "skeptic":
                concerns = _extract_bullet_points(msg["content"], limit=3)

        return CandidateEvaluation(
            candidate_name=candidate.name,
            candidate_id=candidate.candidate_id,
            overall_score=result["overall_score"],
            component_scores=result["component_scores"],
            recommendation=result["final_decision"],
            debate_summary=[
                {"agent": msg["agent"], "role": msg["role"], "summary": msg["content"][:300]}
                for msg in result["debate_transcript"]
            ],
            github_verification=github_verification,
            key_strengths=strengths,
            key_concerns=concerns,
        )


def _extract_bullet_points(text: str, limit: int = 3) -> List[str]:
    """Extract key points from agent text."""
    points = []
    for line in text.split("\n"):
        line = line.strip()
        if line and (line.startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.")) or "✓" in line or "⚠" in line):
            clean = line.lstrip("-*0123456789. ✓⚠️ ")
            if len(clean) > 10:
                points.append(clean[:150])
            if len(points) >= limit:
                break
    return points


__all__ = ["HiringService"]
