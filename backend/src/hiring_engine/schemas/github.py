"""GitHub verification schemas."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class GitHubProfile(BaseModel):
    """Basic GitHub profile information."""

    username: str
    account_age_days: int = 0
    public_repos: int = 0
    followers: int = 0
    following: int = 0
    total_commits_last_year: int = 0
    top_languages: Dict[str, int] = Field(default_factory=dict)
    bio: Optional[str] = None
    company: Optional[str] = None
    hireable: Optional[bool] = None


class CommitPattern(BaseModel):
    """Commit activity pattern analysis."""

    total_commits: int = 0
    active_weeks: int = 0
    consistency_score: float = Field(0.0, ge=0, le=1)
    burst_detected: bool = False
    longest_streak_days: int = 0
    avg_commits_per_active_week: float = 0.0


class RepoAnalysis(BaseModel):
    """Analysis of a single repository."""

    name: str
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    has_readme: bool = False
    has_license: bool = False
    is_fork: bool = False
    last_pushed_days_ago: int = 0
    description: Optional[str] = None


class SkillVerification(BaseModel):
    """Verification of a single claimed skill."""

    skill: str
    verified: bool = False
    evidence_strength: str = "none"  # none, weak, moderate, strong
    repos_found: int = 0
    lines_of_code: int = 0


class CodeQualitySignal(BaseModel):
    """Code quality assessment from repo samples."""

    quality_score: float = Field(0.0, ge=0, le=100)
    structure: str = "unknown"  # poor, basic, good, excellent
    testing_present: bool = False
    documentation_quality: str = "none"  # none, minimal, good, excellent
    is_tutorial_copy: bool = False
    summary: str = ""


class GitHubVerificationResult(BaseModel):
    """Complete GitHub verification result."""

    profile: GitHubProfile
    commit_pattern: CommitPattern
    top_repos: List[RepoAnalysis] = Field(default_factory=list)
    skill_verification: List[SkillVerification] = Field(default_factory=list)
    code_quality: Optional[CodeQualitySignal] = None

    # Trust scoring
    authenticity_score: float = Field(0.0, ge=0, le=100)
    skill_match_score: float = Field(0.0, ge=0, le=100)
    activity_score: float = Field(0.0, ge=0, le=100)
    overall_trust_score: float = Field(0.0, ge=0, le=100)

    trust_label: str = "unknown"  # real_active, real_inactive, suspicious, possibly_fake
    flags: List[str] = Field(default_factory=list)
    analysis_summary: str = ""
