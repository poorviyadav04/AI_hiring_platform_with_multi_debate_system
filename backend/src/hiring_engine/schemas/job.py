"""Job-related schemas."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class JobRequirements(BaseModel):
    """Job role requirements and constraints."""

    job_id: str = Field(..., description="Unique job identifier")
    title: str
    department: str
    level: Literal["junior", "mid", "senior", "staff", "principal"]

    # Requirements
    required_skills: List[str] = Field(..., min_length=1)
    preferred_skills: List[str] = Field(default_factory=list)
    min_experience_years: float = Field(..., ge=0)
    required_education: str

    # Constraints
    budget_min: float = Field(..., gt=0)
    budget_max: float = Field(..., gt=0)
    team_size: int = Field(default=5)
    work_mode: Literal["remote", "hybrid", "onsite"]

    # Context
    urgency: Literal["low", "medium", "high", "critical"] = "medium"
    team_description: Optional[str] = None
    key_responsibilities: List[str] = Field(default_factory=list)
    growth_opportunities: Optional[str] = None

    @field_validator("budget_max")
    @classmethod
    def budget_max_greater_than_min(cls, v: float, info) -> float:
        if "budget_min" in info.data and v < info.data["budget_min"]:
            raise ValueError("budget_max must be >= budget_min")
        return v


class JDParseResult(BaseModel):
    """Result of parsing a job description."""

    job_requirements: JobRequirements
    confidence: float = Field(0.0, ge=0, le=1)
    warnings: List[str] = Field(default_factory=list)
    inferred_fields: List[str] = Field(default_factory=list)
