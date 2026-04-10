"""
Constraint validation functions for hiring decisions.
Ensures decisions comply with policies, budgets, and requirements.
"""

from typing import Dict, List, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from data.schemas import CandidateProfile, JobRequirements, HiringConstraints


def check_budget_constraint(
    candidate_salary: float,
    job_budget_min: float,
    job_budget_max: float,
    max_overage_percent: float = 5.0
) -> Dict[str, any]:
    """
    Validate if candidate's salary expectation fits within budget.
    
    Args:
        candidate_salary: Candidate's expected salary
        job_budget_min: Minimum budget for role
        job_budget_max: Maximum budget for role
        max_overage_percent: Maximum allowed overage (default 5%)
        
    Returns:
        Dict with compliance status, margin, and recommendation
    """
    
    # Calculate budget tolerance
    tolerance = job_budget_max * (max_overage_percent / 100)
    absolute_max = job_budget_max + tolerance
    
    # Check compliance
    within_budget = job_budget_min <= candidate_salary <= job_budget_max
    within_tolerance = job_budget_min <= candidate_salary <= absolute_max
    
    # Calculate margin
    if candidate_salary < job_budget_min:
        margin = job_budget_min - candidate_salary
        margin_percent = (margin / job_budget_min) * 100
        status = "under_budget"
        risk_level = "low"
        explanation = f"Salary ${candidate_salary:,.0f} is below minimum budget (saves ${margin:,.0f})"
    elif candidate_salary <= job_budget_max:
        margin = job_budget_max - candidate_salary
        margin_percent = (margin / job_budget_max) * 100
        status = "within_budget"
        risk_level = "low"
        explanation = f"Salary ${candidate_salary:,.0f} is within budget (${margin:,.0f} margin)"
    elif candidate_salary <= absolute_max:
        margin = candidate_salary - job_budget_max
        margin_percent = (margin / job_budget_max) * 100
        status = "within_tolerance"
        risk_level = "medium"
        explanation = f"Salary ${candidate_salary:,.0f} exceeds budget by ${margin:,.0f} ({margin_percent:.1f}%), within tolerance"
    else:
        margin = candidate_salary - job_budget_max
        margin_percent = (margin / job_budget_max) * 100
        status = "exceeds_tolerance"
        risk_level = "high"
        explanation = f"Salary ${candidate_salary:,.0f} exceeds budget by ${margin:,.0f} ({margin_percent:.1f}%), beyond tolerance"
    
    # Recommendation
    if status == "within_budget":
        recommendation = "approve"
    elif status == "within_tolerance":
        recommendation = "conditional_approve_with_negotiation"
    elif status == "under_budget":
        recommendation = "approve"
    else:
        recommendation = "reject_or_escalate"
    
    return {
        "compliant": within_tolerance,
        "strictly_compliant": within_budget,
        "status": status,
        "risk_level": risk_level,
        "margin": round(abs(margin), 2),
        "margin_percent": round(margin_percent, 2),
        "candidate_salary": candidate_salary,
        "budget_range": (job_budget_min, job_budget_max),
        "absolute_max": absolute_max,
        "recommendation": recommendation,
        "explanation": explanation,
        "requires_vp_approval": candidate_salary > 150000,  # Hardcoded threshold
    }


def validate_experience_requirement(
    candidate_years: float,
    required_years: float,
    allow_gap: bool = True,
    max_gap_years: float = 1.0
) -> Dict[str, any]:
    """
    Validate if candidate meets experience requirements.
    
    Args:
        candidate_years: Candidate's years of experience
        required_years: Required years of experience
        allow_gap: Whether to allow experience gaps
        max_gap_years: Maximum allowed gap
        
    Returns:
        Dict with compliance status
    """
    
    gap = required_years - candidate_years
    
    if candidate_years >= required_years:
        compliant = True
        status = "meets_requirement"
        explanation = f"Candidate has {candidate_years} years (requires {required_years})"
    elif allow_gap and gap <= max_gap_years:
        compliant = True
        status = "within_gap_tolerance"
        explanation = f"Candidate has {candidate_years} years, {gap:.1f} year gap within tolerance"
    else:
        compliant = False
        status = "below_requirement"
        explanation = f"Candidate has {candidate_years} years, {gap:.1f} year gap exceeds policy"
    
    return {
        "compliant": compliant,
        "status": status,
        "gap": round(gap, 2),
        "candidate_years": candidate_years,
        "required_years": required_years,
        "explanation": explanation,
    }


def check_score_thresholds(
    technical_score: Optional[float],
    behavioral_score: Optional[float],
    overall_score: float,
    min_technical: float = 60.0,
    min_behavioral: float = 60.0,
    min_overall: float = 65.0
) -> Dict[str, any]:
    """
    Validate if candidate's scores meet minimum thresholds.
    
    Args:
        technical_score: Technical interview score (0-100)
        behavioral_score: Behavioral interview score (0-100)
        overall_score: Overall calculated score (0-100)
        min_technical: Minimum required technical score
        min_behavioral: Minimum required behavioral score
        min_overall: Minimum required overall score
        
    Returns:
        Dict with compliance and failures
    """
    
    failures = []
    
    # Check technical score
    if technical_score is not None and technical_score < min_technical:
        failures.append({
            "type": "technical_score",
            "value": technical_score,
            "threshold": min_technical,
            "gap": min_technical - technical_score
        })
    
    # Check behavioral score
    if behavioral_score is not None and behavioral_score < min_behavioral:
        failures.append({
            "type": "behavioral_score",
            "value": behavioral_score,
            "threshold": min_behavioral,
            "gap": min_behavioral - behavioral_score
        })
    
    # Check overall score
    if overall_score < min_overall:
        failures.append({
            "type": "overall_score",
            "value": overall_score,
            "threshold": min_overall,
            "gap": min_overall - overall_score
        })
    
    compliant = len(failures) == 0
    
    return {
        "compliant": compliant,
        "failures": failures,
        "failure_count": len(failures),
        "scores": {
            "technical": technical_score,
            "behavioral": behavioral_score,
            "overall": overall_score,
        },
        "thresholds": {
            "technical": min_technical,
            "behavioral": min_behavioral,
            "overall": min_overall,
        },
        "explanation": f"{'Passes' if compliant else 'Fails'} score thresholds ({len(failures)} failure(s))"
    }


def validate_all_constraints(
    candidate: CandidateProfile,
    job: JobRequirements,
    overall_score: float,
    constraints: HiringConstraints
) -> Dict[str, any]:
    """
    Run all constraint checks for a hiring decision.
    
    Args:
        candidate: Candidate profile
        job: Job requirements
        overall_score: Calculated overall score
        constraints: Hiring policies/constraints
        
    Returns:
        Comprehensive validation result
    """
    
    # Budget check
    budget_check = check_budget_constraint(
        candidate.salary_expectation,
        job.budget_min,
        job.budget_max,
        constraints.max_budget_overage_percent
    )
    
    # Experience check
    experience_check = validate_experience_requirement(
        candidate.experience_years,
        job.min_experience_years,
        constraints.allow_experience_gap,
        constraints.max_experience_gap_years
    )
    
    # Score thresholds check
    score_check = check_score_thresholds(
        candidate.technical_interview_score,
        candidate.behavioral_interview_score,
        overall_score,
        constraints.min_technical_score,
        constraints.min_behavioral_score,
        constraints.min_overall_score
    )
    
    # Aggregate results
    all_checks = [budget_check, experience_check, score_check]
    all_compliant = all(check["compliant"] for check in all_checks)
    
    violations = []
    warnings = []
    
    if not budget_check["compliant"]:
        violations.append(f"Budget: {budget_check['explanation']}")
    elif budget_check["status"] == "within_tolerance":
        warnings.append(f"Budget: {budget_check['explanation']}")
    
    if not experience_check["compliant"]:
        violations.append(f"Experience: {experience_check['explanation']}")
    
    if not score_check["compliant"]:
        for failure in score_check["failures"]:
            violations.append(
                f"Score: {failure['type']} ({failure['value']:.1f}) below threshold ({failure['threshold']:.1f})"
            )
    
    # Additional checks
    if budget_check["requires_vp_approval"]:
        warnings.append("Requires VP approval (salary > $150K)")
    
    # Overall compliance rate
    compliance_rate = sum(1 for check in all_checks if check["compliant"]) / len(all_checks)
    
    # Final recommendation
    if all_compliant and len(warnings) == 0:
        final_decision = "approve"
        explanation = "All constraints satisfied"
    elif all_compliant and len(warnings) > 0:
        final_decision = "conditional_approve"
        explanation = f"Compliant with {len(warnings)} warning(s)"
    elif compliance_rate >= 0.66:
        final_decision = "review_required"
        explanation = f"Some violations detected ({len(violations)} violation(s))"
    else:
        final_decision = "reject"
        explanation = f"Multiple violations detected ({len(violations)} violation(s))"
    
    return {
        "all_compliant": all_compliant,
        "compliance_rate": round(compliance_rate, 2),
        "final_decision": final_decision,
        "violations": violations,
        "warnings": warnings,
        "explanation": explanation,
        "detailed_checks": {
            "budget": budget_check,
            "experience": experience_check,
            "scores": score_check,
        },
        "requires_escalation": budget_check["requires_vp_approval"] or not all_compliant,
    }


# Export functions
__all__ = [
    "check_budget_constraint",
    "validate_experience_requirement",
    "check_score_thresholds",
    "validate_all_constraints",
]
