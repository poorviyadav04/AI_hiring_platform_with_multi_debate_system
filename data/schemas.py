"""
Data schemas for the LLM Decision Intelligence System.
Defines structured formats for candidates, jobs, decisions, and constraints.
"""

from datetime import datetime
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, validator


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
    salary_expectation: float = Field(..., gt=0)
    work_preference: Literal["remote", "hybrid", "onsite"] = "hybrid"
    availability_date: Optional[str] = None
    willing_to_relocate: bool = False
    
    # Additional Context
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    notable_projects: List[str] = Field(default_factory=list)
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    
    @validator('skills')
    def skills_not_empty(cls, v):
        if not v:
            raise ValueError('Candidate must have at least one skill')
        return v


class JobRequirements(BaseModel):
    """Job role requirements and constraints."""
    
    job_id: str = Field(..., description="Unique job identifier")
    title: str
    department: str
    level: Literal["junior", "mid", "senior", "staff", "principal"]
    
    # Requirements
    required_skills: List[str] = Field(..., min_items=1)
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
    
    @validator('budget_max')
    def budget_max_greater_than_min(cls, v, values):
        if 'budget_min' in values and v < values['budget_min']:
            raise ValueError('budget_max must be >= budget_min')
        return v


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


class AgentEvaluation(BaseModel):
    """Individual agent's evaluation of a candidate."""
    
    agent_name: str
    agent_role: Literal["technical_evaluator", "culture_fit", "risk_assessor", "moderator", "red_team"]
    
    score: float = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1, description="Agent's confidence in evaluation")
    
    reasoning: str = Field(..., min_length=20)
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    
    tool_calls_made: List[str] = Field(default_factory=list)
    retrieved_context: List[str] = Field(default_factory=list)
    
    timestamp: datetime = Field(default_factory=datetime.now)


class DebateTranscript(BaseModel):
    """Multi-agent debate record."""
    
    session_id: str
    candidate_id: str
    job_id: str
    
    messages: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of {agent, message, timestamp} dicts"
    )
    
    consensus_reached: bool = False
    debate_rounds: int = 0


class CounterfactualExplanation(BaseModel):
    """What-if scenarios that would change the decision."""
    
    feature_changed: str
    original_value: str
    counterfactual_value: str
    
    impact_on_score: float = Field(..., description="Change in overall score")
    would_change_decision: bool
    
    explanation: str
    feasibility: Literal["easy", "moderate", "difficult", "unlikely"]


class Decision(BaseModel):
    """Final hiring decision with full context."""
    
    decision_id: str
    candidate_id: str
    job_id: str
    
    # Decision
    recommendation: Literal["strong_hire", "hire", "conditional_hire", "reject", "strong_reject"]
    overall_score: float = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    
    # Reasoning
    summary: str = Field(..., min_length=50)
    key_strengths: List[str]
    key_concerns: List[str]
    trade_offs_analysis: str
    
    # Agent Evaluations
    agent_evaluations: List[AgentEvaluation]
    debate_transcript: Optional[DebateTranscript] = None
    
    # Red Team Validation
    red_team_challenges: List[str] = Field(default_factory=list)
    challenges_addressed: bool = False
    revision_count: int = 0
    
    # Explainability
    counterfactuals: List[CounterfactualExplanation] = Field(default_factory=list)
    feature_importance: Dict[str, float] = Field(default_factory=dict)
    
    # Constraint Compliance
    constraints_checked: List[str] = Field(default_factory=list)
    constraints_violated: List[str] = Field(default_factory=list)
    compliance_rate: float = Field(1.0, ge=0, le=1)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    processing_time_seconds: Optional[float] = None
    model_used: str = "llama3"
    
    # Feedback Loop
    outcome: Optional[Literal["hired_success", "hired_failure", "rejected_correctly", "rejected_missed_opportunity"]] = None
    outcome_notes: Optional[str] = None
    feedback_received_at: Optional[datetime] = None


class RetrievalContext(BaseModel):
    """Retrieved context from RAG system."""
    
    retrieval_id: str
    query: str
    retrieval_method: Literal["vector_similarity", "graph_traversal", "hybrid"]
    
    # Retrieved Items
    similar_candidates: List[Dict] = Field(default_factory=list)
    similar_decisions: List[Dict] = Field(default_factory=list)
    relevant_constraints: List[Dict] = Field(default_factory=list)
    
    # Metadata
    num_results: int
    retrieval_time_ms: float
    similarity_scores: List[float] = Field(default_factory=list)


# Export all schemas
__all__ = [
    "CandidateProfile",
    "JobRequirements",
    "HiringConstraints",
    "AgentEvaluation",
    "DebateTranscript",
    "CounterfactualExplanation",
    "Decision",
    "RetrievalContext",
]
