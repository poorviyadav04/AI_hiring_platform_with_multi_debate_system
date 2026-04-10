"""
LangChain tool wrappers for scoring and constraint functions.
These tools can be used by LLM agents to call deterministic scoring functions.
"""

from typing import List, Optional
from langchain.tools import tool
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.scoring import (
    calculate_skill_match,
    calculate_experience_score,
    calculate_education_score,
)
from tools.constraints import (
    check_budget_constraint,
    validate_experience_requirement,
    check_score_thresholds,
)


@tool
def skill_match_tool(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: Optional[List[str]] = None
) -> str:
    """
    Calculate how well a candidate's skills match job requirements.
    
    Args:
        candidate_skills: List of candidate's skills (e.g., ["Python", "React", "AWS"])
        required_skills: List of required skills for the job
        preferred_skills: Optional list of preferred skills
        
    Returns:
        Formatted string with skill match analysis including:
        - Overall match score (0-100)
        - Matched and missing required skills
        - Preferred skills matched
        - Depth bonus for extra skills
    """
    
    result = calculate_skill_match(
        candidate_skills=candidate_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills or []
    )
    
    output = f"""Skill Match Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Score: {result['overall_score']}/100

Required Skills Match: {result['required_match_score']}%
  ✓ Matched: {', '.join(result['matched_required']) if result['matched_required'] else 'None'}
  ✗ Missing: {', '.join(result['missing_required']) if result['missing_required'] else 'None'}

Preferred Skills Match: {result['preferred_match_score']}%
  ✓ Matched: {', '.join(result['matched_preferred']) if result['matched_preferred'] else 'None'}

Depth Bonus: +{result['depth_bonus']} points
Match Ratio: {result['match_ratio']:.0%}
"""
    
    return output


@tool
def experience_match_tool(
    candidate_years: float,
    required_years: float,
    role_level: str,
    allow_gap: bool = True,
    max_gap_years: float = 1.0
) -> str:
    """
    Evaluate if candidate's experience meets job requirements.
    
    Args:
        candidate_years: Candidate's years of relevant experience
        required_years: Minimum years required for the job
        role_level: Job level - one of: junior, mid, senior, staff
        allow_gap: Whether to allow experience gaps (default: True)
        max_gap_years: Maximum allowed gap in years (default: 1.0)
        
    Returns:
        Formatted string with experience analysis including:
        - Experience score (0-100)
        - Gap analysis
        - Whether candidate meets minimum requirement
        - Explanation of scoring
    """
    
    result = calculate_experience_score(
        candidate_years=candidate_years,
        required_years=required_years,
        role_level=role_level,
        allow_gap=allow_gap,
        max_gap_years=max_gap_years
    )
    
    meets_emoji = "✓" if result['meets_minimum'] else "✗"
    
    output = f"""Experience Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Score: {result['score']}/100

Candidate Experience: {candidate_years} years
Required Experience: {required_years} years
Gap: {result['gap_years']} years

{meets_emoji} Meets Minimum: {result['meets_minimum']}

Penalty Applied: {result['penalty']} points
Level Multiplier ({role_level}): {result['level_multiplier']}x

Explanation: {result['explanation']}
"""
    
    return output


@tool
def budget_check_tool(
    candidate_salary: float,
    budget_min: float,
    budget_max: float,
    max_overage_percent: float = 5.0
) -> str:
    """
    Check if candidate's salary expectation fits within budget constraints.
    
    Args:
        candidate_salary: Candidate's expected salary
        budget_min: Minimum budget for the role
        budget_max: Maximum budget for the role
        max_overage_percent: Maximum allowed budget overage percentage (default: 5.0)
        
    Returns:
        Formatted string with budget analysis including:
        - Compliance status
        - Budget margin
        - Risk level
        - Recommendation
    """
    
    result = check_budget_constraint(
        candidate_salary=candidate_salary,
        job_budget_min=budget_min,
        job_budget_max=budget_max,
        max_overage_percent=max_overage_percent
    )
    
    status_emoji = "✓" if result['compliant'] else "✗"
    risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(result['risk_level'], "⚪")
    
    output = f"""Budget Constraint Check:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{status_emoji} Compliant: {result['compliant']}
Status: {result['status']}
{risk_emoji} Risk Level: {result['risk_level']}

Candidate Salary: ${candidate_salary:,.0f}
Budget Range: ${budget_min:,.0f} - ${budget_max:,.0f}
Absolute Max (with {max_overage_percent}% tolerance): ${result['absolute_max']:,.0f}

Margin: ${result['margin']:,.0f} ({result['margin_percent']:.1f}%)

Recommendation: {result['recommendation']}
VP Approval Required: {result['requires_vp_approval']}

Explanation: {result['explanation']}
"""
    
    return output


@tool
def score_threshold_check_tool(
    technical_score: Optional[float],
    behavioral_score: Optional[float],
    overall_score: float,
    min_technical: float = 60.0,
    min_behavioral: float = 60.0,
    min_overall: float = 65.0
) -> str:
    """
    Validate if candidate's scores meet minimum thresholds.
    
    Args:
        technical_score: Technical interview score (0-100), can be None
        behavioral_score: Behavioral interview score (0-100), can be None
        overall_score: Overall calculated score (0-100)
        min_technical: Minimum required technical score (default: 60.0)
        min_behavioral: Minimum required behavioral score (default: 60.0)
        min_overall: Minimum required overall score (default: 65.0)
        
    Returns:
        Formatted string with score validation results including:
        - Pass/fail for each score type
        - Gaps from thresholds
        - Overall compliance
    """
    
    result = check_score_thresholds(
        technical_score=technical_score,
        behavioral_score=behavioral_score,
        overall_score=overall_score,
        min_technical=min_technical,
        min_behavioral=min_behavioral,
        min_overall=min_overall
    )
    
    status_emoji = "✓" if result['compliant'] else "✗"
    
    output = f"""Score Threshold Check:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{status_emoji} All Thresholds Met: {result['compliant']}
Failures: {result['failure_count']}

Scores vs Thresholds:
  Technical: {technical_score or 'N/A'} (min: {min_technical})
  Behavioral: {behavioral_score or 'N/A'} (min: {min_behavioral})
  Overall: {overall_score} (min: {min_overall})
"""
    
    if result['failures']:
        output += "\n❌ Failed Checks:\n"
        for failure in result['failures']:
            output += f"  • {failure['type']}: {failure['value']:.1f} is {failure['gap']:.1f} below threshold ({failure['threshold']})\n"
    else:
        output += "\n✅ All scores meet minimum thresholds\n"
    
    return output


# Tool list for easy registration
SCORING_TOOLS = [
    skill_match_tool,
    experience_match_tool,
    budget_check_tool,
    score_threshold_check_tool,
]


__all__ = [
    "skill_match_tool",
    "experience_match_tool",
    "budget_check_tool",
    "score_threshold_check_tool",
    "SCORING_TOOLS",
]
