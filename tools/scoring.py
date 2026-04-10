"""
Deterministic scoring functions for candidate evaluation.
Scoring utilities for candidate evaluation.
Now MCP-aware: uses MCP registry internally for tool discovery.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from data.schemas import CandidateProfile, JobRequirements


def calculate_overall_score_detailed(
    candidate: CandidateProfile,
    job: JobRequirements
) -> Dict[str, Any]:
    """
    Calculate comprehensive candidate score with detailed breakdown.
    This is the original implementation used as fallback.
    
    Args:
        candidate: Candidate profile
        job: Job requirements
        
    Returns:
        Dict containing:
        - overall_score: Weighted final score
        - component_scores: Individual category scores
        - detailed_breakdown: Detailed analysis per category
        - recommendation: hire/conditional_hire/reject
    """
    try:
        from mcp_servers import get_registry
        
        registry = get_registry()
        
        # Call scoring tools via MCP protocol
        result = registry.execute(
            "scoring",
            "calculate_overall_score_full",  # Full scoring with breakdown
            candidate=candidate,
            job=job
        )
        
        return result
        
    except Exception as e:
        # Fallback to direct implementation if MCP not available
        print(f"⚠️ MCP scoring unavailable, using fallback: {e}")
        return _calculate_overall_score_fallback(candidate, job)


def _calculate_overall_score_fallback(
    candidate: CandidateProfile,
    job: JobRequirements
) -> Dict[str, Any]:
    """
    Fallback overall score calculation when MCP is not available.
    This function directly calls the deterministic scoring functions.
    """
    
    # Skill Match
    skill_match_results = calculate_skill_match(
        candidate_skills=candidate.skills,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills
    )
    
    # Experience Score
    experience_results = calculate_experience_score(
        candidate_years=candidate.years_experience,
        required_years=job.required_years_experience,
        role_level=job.role_level,
        allow_gap=True, # Assuming default allowance for fallback
        max_gap_years=1.0 # Assuming default tolerance for fallback
    )
    
    # Education Score
    education_results = calculate_education_score(
        candidate_education=candidate.education_level,
        required_education=job.required_education_level
    )
    
    # Combine scores (example weighting)
    overall_score = (
        skill_match_results["overall_score"] * 0.5 +
        experience_results["score"] * 0.4 +
        education_results["score"] * 0.1
    )
    
    return {
        "overall_score": round(overall_score, 2),
        "skill_match": skill_match_results,
        "experience": experience_results,
        "education": education_results,
        "summary": "Scores calculated using fallback deterministic functions."
    }


def calculate_skill_match(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: Optional[List[str]] = None,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Calculate skill match score between candidate and job requirements.
    
    Algorithm:
    1. Required skills match: 70% weight
    2. Preferred skills match: 30% weight
    3. Bonus for depth (number of skills beyond required)
    
    Args:
        candidate_skills: List of candidate's skills
        required_skills: Must-have skills for the job
        preferred_skills: Nice-to-have skills
        weights: Optional custom weights for specific skills
        
    Returns:
        Dict with:
            - overall_score: 0-100
            - required_match_score: 0-100
            - preferred_match_score: 0-100
            - matched_required: List of matched required skills
            - matched_preferred: List of matched preferred skills
            - missing_required: List of missing required skills
            - depth_bonus: Extra points for skill breadth
    """
    
    if not required_skills:
        raise ValueError("required_skills cannot be empty")
    
    # Normalize skills to lowercase for case-insensitive matching
    candidate_skills_lower = [s.lower() for s in candidate_skills]
    required_skills_lower = [s.lower() for s in required_skills]
    preferred_skills_lower = [s.lower() for s in (preferred_skills or [])]
    
    # Match required skills
    matched_required = []
    missing_required = []
    
    for skill in required_skills:
        if skill.lower() in candidate_skills_lower:
            matched_required.append(skill)
        else:
            missing_required.append(skill)
    
    # Calculate required skills match percentage
    required_match_ratio = len(matched_required) / len(required_skills)
    required_match_score = required_match_ratio * 100
    
    # Match preferred skills
    matched_preferred = []
    if preferred_skills:
        for skill in preferred_skills:
            if skill.lower() in candidate_skills_lower:
                matched_preferred.append(skill)
        
        preferred_match_ratio = len(matched_preferred) / len(preferred_skills)
        preferred_match_score = preferred_match_ratio * 100
    else:
        preferred_match_score = 0
    
    # Calculate overall score with weighting
    # Required: 70%, Preferred: 30%
    overall_score = (required_match_score * 0.7) + (preferred_match_score * 0.3)
    
    # Depth bonus: Extra points for having many skills beyond requirements
    total_required = len(required_skills) + len(preferred_skills or [])
    extra_skills = max(0, len(candidate_skills) - total_required)
    depth_bonus = min(10, extra_skills * 2)  # Max 10 bonus points
    
    # Add depth bonus to overall score (capped at 100)
    overall_score = min(100, overall_score + depth_bonus)
    
    return {
        "overall_score": round(overall_score, 2),
        "required_match_score": round(required_match_score, 2),
        "preferred_match_score": round(preferred_match_score, 2),
        "matched_required": matched_required,
        "matched_preferred": matched_preferred,
        "missing_required": missing_required,
        "depth_bonus": round(depth_bonus, 2),
        "match_ratio": round(required_match_ratio, 2),
    }


def calculate_experience_score(
    candidate_years: float,
    required_years: float,
    role_level: str,
    allow_gap: bool = True,
    max_gap_years: float = 1.0
) -> Dict[str, float]:
    """
    Score candidate's experience relative to job requirements.
    
    Algorithm:
    1. Perfect match (within 0.5 years): 100 points
    2. Overqualified (2x+ experience): 90-95 points (slight penalty for potential flight risk)
    3. Underqualified: Penalty based on gap size
    4. Gap within tolerance: 80-95 points
    
    Args:
        candidate_years: Candidate's years of experience
        required_years: Minimum required experience
        role_level: junior | mid | senior | staff
        allow_gap: Whether to allow experience gaps
        max_gap_years: Maximum allowed gap if allow_gap is True
        
    Returns:
        Dict with score, gap, penalty info
    """
    
    gap = required_years - candidate_years
    
    # Perfect match or slightly over
    if abs(gap) <= 0.5:
        score = 100
        penalty = 0
        explanation = "Perfect experience match"
    
    # Candidate exceeds requirements
    elif candidate_years > required_years:
        excess_ratio = candidate_years / max(required_years, 0.1)
        
        if excess_ratio >= 2.0:
            # Significantly overqualified - slight penalty for potential retention risk
            score = 90
            penalty = 10
            explanation = "Overqualified - potential retention risk"
        elif excess_ratio >= 1.5:
            score = 95
            penalty = 5
            explanation = "Slightly overqualified"
        else:
            score = 100
            penalty = 0
            explanation = "Exceeds requirements appropriately"
    
    # Candidate has less experience than required
    else:
        if not allow_gap:
            score = max(0, 100 - (gap * 20))  # 20 points per year gap
            penalty = min(100, gap * 20)
            explanation = f"Below requirements by {gap:.1f} years (gap not allowed)"
        elif gap <= max_gap_years:
            # Acceptable gap
            penalty_per_year = 15  # More lenient than when gaps not allowed
            penalty = gap * penalty_per_year
            score = max(60, 100 - penalty)
            explanation = f"Slightly below requirements ({gap:.1f} years gap, within tolerance)"
        else:
            # Beyond tolerance
            penalty_per_year = 20
            penalty = gap * penalty_per_year
            score = max(40, 100 - penalty)
            explanation = f"Below requirements by {gap:.1f} years (exceeds {max_gap_years} year tolerance)"
    
    # Level-specific adjustments
    level_multipliers = {
        "junior": 1.1,      # More lenient for junior roles
        "mid": 1.0,         # Standard
        "senior": 0.95,     # Stricter for senior roles
        "staff": 0.9,       # Very strict for staff+ roles
    }
    
    multiplier = level_multipliers.get(role_level, 1.0)
    adjusted_score = score * multiplier
    
    return {
        "score": round(min(100, adjusted_score), 2),
        "raw_score": round(score, 2),
        "gap_years": round(gap, 2),
        "penalty": round(penalty, 2),
        "level_multiplier": multiplier,
        "explanation": explanation,
        "meets_minimum": candidate_years >= required_years or (allow_gap and gap <= max_gap_years)
    }


def calculate_education_score(
    candidate_education: str,
    required_education: str
) -> Dict[str, float]:
    """
    Score candidate's education relative to requirements.
    
    Education hierarchy (ascending):
    1. High School
    2. Associate Degree
    3. Bootcamp
    4. BS/BA
    5. MS
    6. PhD
    
    Args:
        candidate_education: Candidate's highest degree
        required_education: Required education level
        
    Returns:
        Dict with score and comparison
    """
    
    # Define education levels and their scores
    education_levels = {
        "high school": 1,
        "associate": 2,
        "bootcamp": 3,
        "bs": 4,
        "ba": 4,
        "bachelor": 4,
        "ms": 5,
        "master": 5,
        "phd": 6,
        "doctorate": 6,
    }
    
    def get_education_level(education: str) -> int:
        """Extract education level from string."""
        education_lower = education.lower()
        
        if "phd" in education_lower or "doctorate" in education_lower:
            return 6
        elif "ms" in education_lower or "master" in education_lower:
            return 5
        elif "bs" in education_lower or "ba" in education_lower or "bachelor" in education_lower:
            return 4
        elif "bootcamp" in education_lower:
            return 3
        elif "associate" in education_lower:
            return 2
        else:
            return 1
    
    candidate_level = get_education_level(candidate_education)
    required_level = get_education_level(required_education)
    
    # "or equivalent" in requirements makes it more flexible
    is_flexible = "equivalent" in required_education.lower() or "preferred" in required_education.lower()
    
    difference = candidate_level - required_level
    
    # Calculate score
    if difference >= 0:
        # Meets or exceeds requirements
        if difference == 0:
            score = 100
            explanation = "Exact match"
        elif difference == 1:
            score = 100
            explanation = "Exceeds requirements by one level"
        else:
            score = 95
            explanation = "Significantly exceeds requirements"
    else:
        # Below requirements
        if is_flexible:
            # More lenient if "or equivalent" is mentioned
            if difference == -1:
                score = 85
                explanation = "One level below, but 'equivalent' accepted"
            else:
                score = 70
                explanation = "Below requirements, but 'equivalent' may be considered"
        else:
            # Strict requirements
            penalty = abs(difference) * 20
            score = max(30, 100 - penalty)
            explanation = f"Below requirements by {abs(difference)} level(s)"
    
    return {
        "score": round(score, 2),
        "candidate_level": candidate_level,
        "required_level": required_level,
        "difference": difference,
        "meets_requirement": difference >= 0 or (is_flexible and difference >= -1),
        "explanation": explanation
    }


def calculate_overall_score(
    candidate: CandidateProfile,
    job: JobRequirements,
    allow_experience_gap: bool = True,
    max_experience_gap: float = 1.0
) -> Dict[str, any]:
    """
    Calculate comprehensive overall score for a candidate.
    
    Weighting:
    - Skills: 40%
    - Experience: 30%
    - Education: 15%
    - Interview scores: 15% (if available)
    
    Args:
        candidate: Candidate profile
        job: Job requirements
        allow_experience_gap: Whether to allow experience gaps
        max_experience_gap: Maximum allowed gap
        
    Returns:
        Dict with overall score and component breakdown
    """
    
    # Calculate component scores
    skill_result = calculate_skill_match(
        candidate.skills,
        job.required_skills,
        job.preferred_skills
    )
    
    experience_result = calculate_experience_score(
        candidate.experience_years,
        job.min_experience_years,
        job.level,
        allow_experience_gap,
        max_experience_gap
    )
    
    education_result = calculate_education_score(
        candidate.education,
        job.required_education
    )
    
    # Interview scores (if available)
    interview_scores = []
    if candidate.technical_interview_score is not None:
        interview_scores.append(candidate.technical_interview_score)
    if candidate.behavioral_interview_score is not None:
        interview_scores.append(candidate.behavioral_interview_score)
    if candidate.coding_challenge_score is not None:
        interview_scores.append(candidate.coding_challenge_score)
    
    avg_interview_score = sum(interview_scores) / len(interview_scores) if interview_scores else 75
    
    # Calculate weighted overall score
    weights = {
        "skills": 0.40,
        "experience": 0.30,
        "education": 0.15,
        "interviews": 0.15,
    }
    
    overall_score = (
        skill_result["overall_score"] * weights["skills"] +
        experience_result["score"] * weights["experience"] +
        education_result["score"] * weights["education"] +
        avg_interview_score * weights["interviews"]
    )
    
    # Determine recommendation tier
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
            "interviews": round(avg_interview_score, 2),
        },
        "weights": weights,
        "detailed_breakdown": {
            "skills": skill_result,
            "experience": experience_result,
            "education": education_result,
            "interview_count": len(interview_scores),
        },
        "key_factors": {
            "missing_required_skills": skill_result["missing_required"],
            "experience_gap": experience_result["gap_years"],
            "education_gap": education_result["difference"],
        }
    }


# Export functions for MCP server usage
__all__ = [
    "calculate_skill_match",
    "calculate_experience_score",
    "calculate_education_score",
    "calculate_overall_score",
]
