"""Candidate-related schemas."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class CandidateProfile(BaseModel):
    """Structured candidate profile."""

    candidate_id: str = Field(..., description="Unique identifier")
    name: str
    email: str
    phone: Optional[str] = None

    # Technical Information
    skills: List[str] = Field(..., description="Technical and soft skills")
    experience_years: float = Field(..., ge=0, description="Years of relevant experience")
    education: str = Field(..., description="Highest degree obtained")
    certifications: List[str] = Field(default_factory=list)

    # Scores
    technical_interview_score: Optional[float] = Field(None, ge=0, le=100)
    behavioral_interview_score: Optional[float] = Field(None, ge=0, le=100)
    coding_challenge_score: Optional[float] = Field(None, ge=0, le=100)

    # Preferences
    salary_expectation: float = Field(0, ge=0)
    work_preference: Literal["remote", "hybrid", "onsite"] = "hybrid"
    availability_date: Optional[str] = None
    willing_to_relocate: bool = False

    # Additional Context
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    notable_projects: List[str] = Field(default_factory=list)
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None

    @field_validator("skills")
    @classmethod
    def skills_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Candidate must have at least one skill")
        return v


class ResumeParseResult(BaseModel):
    """Result of parsing a resume PDF."""

    candidate_profile: CandidateProfile
    raw_text: str = ""
    confidence: float = Field(0.0, ge=0, le=1)
    warnings: List[str] = Field(default_factory=list)
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
