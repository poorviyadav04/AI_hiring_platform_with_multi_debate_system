"""Candidate-side service — orchestrates the 'Where Do I Stand?' flow."""

import logging
from typing import Dict, Any, List

from hiring_engine.llm.base import BaseLLMClient
from hiring_engine.parsers.resume_parser import parse_resume
from hiring_engine.parsers.jd_parser import parse_job_description
from hiring_engine.scoring.overall import calculate_overall_score
from hiring_engine.scoring.skill_matcher import SkillMatcher
from hiring_engine.scoring.gap_analysis import GapAnalyzer
from hiring_engine.counterfactuals.generator import CounterfactualGenerator
from hiring_engine.schemas.api_models import CandidateAnalysisResult
from hiring_engine.schemas.constraints import HiringConstraints

logger = logging.getLogger(__name__)


class CandidateService:
    """Orchestrates the candidate-side analysis flow."""

    def __init__(self, llm: BaseLLMClient, skill_matcher: SkillMatcher | None = None):
        self._llm = llm
        self._skill_matcher = skill_matcher
        self._gap_analyzer = GapAnalyzer(skill_matcher=skill_matcher)
        self._cf_generator = CounterfactualGenerator(skill_matcher=skill_matcher)
        self._constraints = HiringConstraints(
            policy_id="POL-DEFAULT", policy_name="Standard Hiring Policy"
        )

    async def analyze(
        self, resume_pdf: bytes, jd_text: str
    ) -> CandidateAnalysisResult:
        """Full candidate analysis: parse -> score -> gaps -> roadmap."""
        logger.info("Starting candidate analysis")

        # Step 1: Parse resume and JD
        resume_result = await parse_resume(resume_pdf, self._llm)
        jd_result = await parse_job_description(jd_text, self._llm)

        candidate = resume_result.candidate_profile
        job = jd_result.job_requirements

        logger.info(
            "Parsed: candidate=%s job=%s", candidate.name, job.title
        )
        logger.info("Candidate skills: %s", candidate.skills)
        logger.info("JD required_skills: %s", job.required_skills)
        logger.info("JD preferred_skills: %s", job.preferred_skills)

        # Step 2: Score
        score_result = calculate_overall_score(
            candidate, job, skill_matcher=self._skill_matcher
        )
        logger.info("Score: %.1f (%s)", score_result["overall_score"], score_result["recommendation"])

        # Step 3: Gap analysis
        gaps = self._gap_analyzer.analyze_gaps(candidate, job)

        # Step 4: Counterfactuals
        cf_result = self._cf_generator.generate_overall_counterfactuals(candidate, job, top_k=5)
        counterfactuals = [
            {
                "change": cf["change"],
                "type": cf["type"],
                "current_score": cf.get("overall_current", 0),
                "new_score": cf.get("overall_new", 0),
                "impact": cf.get("overall_impact", 0),
            }
            for cf in cf_result["counterfactuals"]
        ]

        # Step 5: Roadmap
        roadmap = await self._gap_analyzer.generate_roadmap(candidate, job, gaps, self._llm)

        # Collect warnings
        warnings = resume_result.warnings + jd_result.warnings

        return CandidateAnalysisResult(
            score_card=score_result,
            recommendation=score_result["recommendation"],
            gaps=gaps,
            counterfactuals=counterfactuals,
            roadmap=roadmap,
            parse_warnings=warnings,
        )


__all__ = ["CandidateService"]
