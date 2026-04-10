"""Skill matching scoring — supports exact and semantic matching."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from hiring_engine.scoring.skill_matcher import SkillMatcher

logger = logging.getLogger(__name__)


def calculate_skill_match(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: Optional[List[str]] = None,
    weights: Optional[Dict[str, float]] = None,
    skill_matcher: Optional["SkillMatcher"] = None,
) -> Dict[str, float]:
    """
    Calculate skill match score between candidate and job requirements.

    If *skill_matcher* is provided, uses semantic embedding similarity.
    Otherwise falls back to exact (case-insensitive) string matching.

    Weighting: Required 70%, Preferred 30%, Depth bonus up to 10 points.
    """
    if not required_skills:
        raise ValueError("required_skills cannot be empty")

    if skill_matcher is not None:
        return _semantic_match(
            candidate_skills, required_skills, preferred_skills, skill_matcher
        )
    return _exact_match(candidate_skills, required_skills, preferred_skills)


def _semantic_match(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: Optional[List[str]],
    matcher: "SkillMatcher",
) -> Dict[str, float]:
    """Embedding-based matching via SkillMatcher."""
    result = matcher.match_skills(candidate_skills, required_skills, preferred_skills)

    required_match_score = result["required_score"]
    preferred_match_score = result["preferred_score"]

    overall_score = (required_match_score * 0.7) + (preferred_match_score * 0.3)

    # Depth bonus: extra skills beyond what's required/preferred
    total_target = len(required_skills) + len(preferred_skills or [])
    extra_skills = max(0, len(candidate_skills) - total_target)
    depth_bonus = min(10, extra_skills * 2)
    overall_score = min(100, overall_score + depth_bonus)

    # Build matched_required list (skills above partial threshold)
    matched_required = [
        m["skill"]
        for m in result["required_matches"]
        if m["match_type"] in ("full", "partial")
    ]
    missing_required = result["missing_required"]

    matched_preferred = [
        m["skill"]
        for m in result["preferred_matches"]
        if m["match_type"] in ("full", "partial")
    ]

    return {
        "overall_score": round(overall_score, 2),
        "required_match_score": round(required_match_score, 2),
        "preferred_match_score": round(preferred_match_score, 2),
        "matched_required": matched_required,
        "matched_preferred": matched_preferred,
        "missing_required": missing_required,
        "depth_bonus": round(depth_bonus, 2),
        "match_ratio": round(len(matched_required) / len(required_skills), 2),
        # Extra detail for downstream consumers
        "semantic_details": result["required_matches"],
    }


def _exact_match(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: Optional[List[str]],
) -> Dict[str, float]:
    """Original exact (case-insensitive) string matching — used as fallback."""
    candidate_skills_lower = [s.lower() for s in candidate_skills]
    matched_required = [s for s in required_skills if s.lower() in candidate_skills_lower]
    missing_required = [s for s in required_skills if s.lower() not in candidate_skills_lower]

    required_match_score = (len(matched_required) / len(required_skills)) * 100

    matched_preferred = []
    preferred_match_score = 0.0
    if preferred_skills:
        matched_preferred = [s for s in preferred_skills if s.lower() in candidate_skills_lower]
        preferred_match_score = (len(matched_preferred) / len(preferred_skills)) * 100

    overall_score = (required_match_score * 0.7) + (preferred_match_score * 0.3)

    total_required = len(required_skills) + len(preferred_skills or [])
    extra_skills = max(0, len(candidate_skills) - total_required)
    depth_bonus = min(10, extra_skills * 2)
    overall_score = min(100, overall_score + depth_bonus)

    return {
        "overall_score": round(overall_score, 2),
        "required_match_score": round(required_match_score, 2),
        "preferred_match_score": round(preferred_match_score, 2),
        "matched_required": matched_required,
        "matched_preferred": matched_preferred,
        "missing_required": missing_required,
        "depth_bonus": round(depth_bonus, 2),
        "match_ratio": round(len(matched_required) / len(required_skills), 2),
    }
