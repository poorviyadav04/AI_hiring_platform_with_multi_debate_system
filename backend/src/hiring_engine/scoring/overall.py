"""Overall candidate scoring — combines all components."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Any, Optional

from hiring_engine.schemas.candidate import CandidateProfile
from hiring_engine.schemas.job import JobRequirements
from hiring_engine.scoring.skills import calculate_skill_match
from hiring_engine.scoring.experience import calculate_experience_score
from hiring_engine.scoring.education import calculate_education_score

if TYPE_CHECKING:
    from hiring_engine.scoring.skill_matcher import SkillMatcher

logger = logging.getLogger(__name__)


def calculate_overall_score(
    candidate: CandidateProfile,
    job: JobRequirements,
    allow_experience_gap: bool = True,
    max_experience_gap: float = 1.0,
    skill_matcher: Optional["SkillMatcher"] = None,
) -> Dict[str, Any]:
    """
    Calculate comprehensive overall score.

    Weights: Skills 50%, Experience 35%, Education 15%.
    """
    skill_result = calculate_skill_match(
        candidate.skills, job.required_skills, job.preferred_skills,
        skill_matcher=skill_matcher,
    )

    experience_result = calculate_experience_score(
        candidate.experience_years,
        job.min_experience_years,
        job.level,
        allow_experience_gap,
        max_experience_gap,
    )

    education_result = calculate_education_score(candidate.education, job.required_education)

    weights = {"skills": 0.50, "experience": 0.35, "education": 0.15}

    overall_score = (
        skill_result["overall_score"] * weights["skills"]
        + experience_result["score"] * weights["experience"]
        + education_result["score"] * weights["education"]
    )

    if overall_score >= 85:
        recommendation = "strong_hire"
    elif overall_score >= 75:
        recommendation = "hire"
    elif overall_score >= 65:
        recommendation = "conditional_hire"
    elif overall_score >= 50:
        recommendation = "reject"
    else:
        recommendation = "strong_reject"

    return {
        "overall_score": round(overall_score, 2),
        "recommendation": recommendation,
        "component_scores": {
            "skills": skill_result["overall_score"],
            "experience": experience_result["score"],
            "education": education_result["score"],
        },
        "weights": weights,
        "detailed_breakdown": {
            "skills": skill_result,
            "experience": experience_result,
            "education": education_result,
        },
        "key_factors": {
            "missing_required_skills": skill_result["missing_required"],
            "experience_gap": experience_result["gap_years"],
            "education_gap": education_result["difference"],
        },
    }
