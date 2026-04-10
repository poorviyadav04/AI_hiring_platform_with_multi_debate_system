"""Evaluation and decision schemas."""

from datetime import datetime
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field


class AgentEvaluation(BaseModel):
    """Individual agent's evaluation of a candidate."""

    agent_name: str
    agent_role: Literal[
        "technical_evaluator", "culture_fit", "risk_assessor", "moderator", "red_team"
    ]
    score: float = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
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
    messages: List[Dict[str, str]] = Field(default_factory=list)
    consensus_reached: bool = False
    debate_rounds: int = 0


class CounterfactualExplanation(BaseModel):
    """What-if scenarios that would change the decision."""

    feature_changed: str
    original_value: str
    counterfactual_value: str
    impact_on_score: float
    would_change_decision: bool
    explanation: str
    feasibility: Literal["easy", "moderate", "difficult", "unlikely"]


class Decision(BaseModel):
    """Final hiring decision with full context."""

    decision_id: str
    candidate_id: str
    job_id: str

    recommendation: Literal[
        "strong_hire", "hire", "conditional_hire", "reject", "strong_reject"
    ]
    overall_score: float = Field(..., ge=0, le=100)
    confidence: float = Field(0.8, ge=0, le=1)

    summary: str = ""
    key_strengths: List[str] = Field(default_factory=list)
    key_concerns: List[str] = Field(default_factory=list)
    trade_offs_analysis: str = ""

    agent_evaluations: List[AgentEvaluation] = Field(default_factory=list)
    debate_transcript: Optional[DebateTranscript] = None

    red_team_challenges: List[str] = Field(default_factory=list)
    challenges_addressed: bool = False
    revision_count: int = 0

    counterfactuals: List[CounterfactualExplanation] = Field(default_factory=list)
    feature_importance: Dict[str, float] = Field(default_factory=dict)

    constraints_checked: List[str] = Field(default_factory=list)
    constraints_violated: List[str] = Field(default_factory=list)
    compliance_rate: float = Field(1.0, ge=0, le=1)

    created_at: datetime = Field(default_factory=datetime.now)
    processing_time_seconds: Optional[float] = None
    model_used: str = "gemini-2.0-flash"

    outcome: Optional[
        Literal[
            "hired_success", "hired_failure", "rejected_correctly", "rejected_missed_opportunity"
        ]
    ] = None
    outcome_notes: Optional[str] = None
    feedback_received_at: Optional[datetime] = None


class RetrievalContext(BaseModel):
    """Retrieved context from RAG system."""

    retrieval_id: str
    query: str
    retrieval_method: Literal["vector_similarity", "graph_traversal", "hybrid"]
    similar_candidates: List[Dict] = Field(default_factory=list)
    similar_decisions: List[Dict] = Field(default_factory=list)
    relevant_constraints: List[Dict] = Field(default_factory=list)
    num_results: int = 0
    retrieval_time_ms: float = 0.0
    similarity_scores: List[float] = Field(default_factory=list)
