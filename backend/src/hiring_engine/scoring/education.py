"""Education scoring."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def _get_education_level(education: str) -> int:
    """Extract education level from string."""
    edu = education.lower()
    if "phd" in edu or "doctorate" in edu:
        return 6
    elif "ms" in edu or "master" in edu:
        return 5
    elif "bs" in edu or "ba" in edu or "bachelor" in edu:
        return 4
    elif "bootcamp" in edu:
        return 3
    elif "associate" in edu:
        return 2
    return 1


def calculate_education_score(
    candidate_education: str,
    required_education: str,
) -> Dict[str, float]:
    """
    Score candidate's education relative to requirements.

    Hierarchy: HS(1) → Associate(2) → Bootcamp(3) → BS/BA(4) → MS(5) → PhD(6).
    """
    candidate_level = _get_education_level(candidate_education)
    required_level = _get_education_level(required_education)
    is_flexible = "equivalent" in required_education.lower() or "preferred" in required_education.lower()
    difference = candidate_level - required_level

    if difference >= 0:
        score = 100 if difference <= 1 else 95
        explanation = "Exact match" if difference == 0 else (
            "Exceeds requirements by one level" if difference == 1 else "Significantly exceeds requirements"
        )
    elif is_flexible:
        score = 85 if difference == -1 else 70
        explanation = (
            "One level below, but 'equivalent' accepted"
            if difference == -1
            else "Below requirements, but 'equivalent' may be considered"
        )
    else:
        penalty = abs(difference) * 20
        score = max(30, 100 - penalty)
        explanation = f"Below requirements by {abs(difference)} level(s)"

    return {
        "score": round(score, 2),
        "candidate_level": candidate_level,
        "required_level": required_level,
        "difference": difference,
        "meets_requirement": difference >= 0 or (is_flexible and difference >= -1),
        "explanation": explanation,
    }
