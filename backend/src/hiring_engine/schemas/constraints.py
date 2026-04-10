"""Hiring constraint schemas."""

from pydantic import BaseModel, Field


class HiringConstraints(BaseModel):
    """System-wide hiring policies and constraints."""

    policy_id: str
    policy_name: str

    # Budget Policies
    max_budget_overage_percent: float = Field(5.0, ge=0, le=20)
    require_vp_approval_above: float = Field(150000)

    # Experience Policies
    allow_experience_gap: bool = True
    max_experience_gap_years: float = Field(1.0, ge=0)

    # Compliance
    require_work_authorization: bool = True
    require_background_check: bool = True
    equal_opportunity_employer: bool = True

    # Preference Policies
    prioritize_internal_candidates: bool = True
    diversity_hiring_goals: bool = True

    # Scoring Thresholds
    min_technical_score: float = Field(60.0, ge=0, le=100)
    min_behavioral_score: float = Field(60.0, ge=0, le=100)
    min_overall_score: float = Field(65.0, ge=0, le=100)
