"""API request/response models."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator

from hiring_engine.schemas.github import GitHubVerificationResult


class CandidateAnalyzeRequest(BaseModel):
    """Request for candidate-side analysis."""

    job_description: str = Field(..., min_length=50)


class GapItem(BaseModel):
    """A single skill/experience gap."""

    category: str  # skill, experience, education
    item: str
    severity: str  # critical, moderate, minor
    impact_points: float
    suggestion: str


class RoadmapItem(BaseModel):
    """A single learning roadmap item."""

    skill: str
    priority: str  # high, medium, low
    estimated_weeks: int = Field(ge=1, le=52)
    resources: List[str] = Field(default_factory=list)
    impact_on_score: float = 0.0

    @field_validator("estimated_weeks", mode="before")
    @classmethod
    def clamp_weeks(cls, v: int) -> int:
        """Clamp to 1-52 so LLM hallucinations don't leak through."""
        if isinstance(v, (int, float)):
            return max(1, min(52, int(v)))
        return v


class CandidateAnalysisResult(BaseModel):
    """Full candidate analysis response."""

    score_card: Dict[str, Any]
    recommendation: str
    gaps: List[GapItem] = Field(default_factory=list)
    counterfactuals: List[Dict[str, Any]] = Field(default_factory=list)
    roadmap: List[RoadmapItem] = Field(default_factory=list)
    parse_warnings: List[str] = Field(default_factory=list)


class HiringEvaluateRequest(BaseModel):
    """Request for hiring team evaluation."""

    job_description: str = Field(..., min_length=50)


class CandidateEvaluation(BaseModel):
    """Single candidate evaluation in hiring flow."""

    candidate_name: str
    candidate_id: str
    overall_score: float
    component_scores: Dict[str, float]
    recommendation: str
    debate_summary: List[Dict[str, str]]
    github_verification: Optional[GitHubVerificationResult] = None
    key_strengths: List[str] = Field(default_factory=list)
    key_concerns: List[str] = Field(default_factory=list)


class HiringEvaluationResult(BaseModel):
    """Full hiring team evaluation response."""

    job_title: str
    job_id: str
    total_candidates: int
    rankings: List[CandidateEvaluation]
    evaluation_id: str


class GitHubVerifyRequest(BaseModel):
    """Request to verify a GitHub profile."""

    github_url: str
    claimed_skills: List[str] = Field(default_factory=list)


class CompareRequest(BaseModel):
    """Request to compare candidates."""

    evaluation_ids: List[str] = Field(..., min_length=2, max_length=5)
