"""Experience scoring."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def calculate_experience_score(
    candidate_years: float,
    required_years: float,
    role_level: str,
    allow_gap: bool = True,
    max_gap_years: float = 1.0,
) -> Dict[str, float]:
    """
    Score candidate's experience relative to job requirements.

    Perfect match: 100, Overqualified 2x: 90, Underqualified: penalty-based.
    Level multipliers: junior=1.1, mid=1.0, senior=0.95, staff=0.9.
    """
    gap = required_years - candidate_years

    if abs(gap) <= 0.5:
        score, penalty = 100, 0
        explanation = "Perfect experience match"
    elif candidate_years > required_years:
        excess_ratio = candidate_years / max(required_years, 0.1)
        if excess_ratio >= 2.0:
            score, penalty = 90, 10
            explanation = "Overqualified - potential retention risk"
        elif excess_ratio >= 1.5:
            score, penalty = 95, 5
            explanation = "Slightly overqualified"
        else:
            score, penalty = 100, 0
            explanation = "Exceeds requirements appropriately"
    else:
        if not allow_gap:
            score = max(0, 100 - (gap * 20))
            penalty = min(100, gap * 20)
            explanation = f"Below requirements by {gap:.1f} years (gap not allowed)"
        elif gap <= max_gap_years:
            penalty = gap * 15
            score = max(60, 100 - penalty)
            explanation = f"Slightly below requirements ({gap:.1f} years gap, within tolerance)"
        else:
            penalty = gap * 20
            score = max(40, 100 - penalty)
            explanation = f"Below requirements by {gap:.1f} years (exceeds {max_gap_years} year tolerance)"

    level_multipliers = {"junior": 1.1, "mid": 1.0, "senior": 0.95, "staff": 0.9, "principal": 0.85}
    multiplier = level_multipliers.get(role_level, 1.0)
    adjusted_score = score * multiplier

    return {
        "score": round(min(100, adjusted_score), 2),
        "raw_score": round(score, 2),
        "gap_years": round(gap, 2),
        "penalty": round(penalty, 2),
        "level_multiplier": multiplier,
        "explanation": explanation,
        "meets_minimum": candidate_years >= required_years
        or (allow_gap and gap <= max_gap_years),
    }
