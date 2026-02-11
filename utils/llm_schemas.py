"""
LLM Response Schemas for Structured Output

Pydantic schemas that enforce structured, validated responses from LLM calls.
Ensures agents return consistent, parseable output with confidence scores.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class AgentResponse(BaseModel):
    """Base schema for all agent responses."""
    agent_name: str = Field(..., description="Name of the agent")
    content: str = Field(..., description="Main response content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: Optional[str] = Field(None, description="Step-by-step reasoning")


class AdvocateResponse(BaseModel):
    """Structured response from Advocate agent."""
    strengths: List[str] = Field(..., min_items=1, description="Candidate strengths")
    growth_opportunities: List[str] = Field(default_factory=list, description="Areas for development")
    hire_recommendation: bool = Field(..., description="Recommends hiring")
    confidence: float = Field(..., ge=0.0, le=1.0)
    key_argument: str = Field(..., description="Main argument for hiring")
    mitigations: Optional[List[str]] = Field(default_factory=list, description="Risk mitigations")


class SkepticResponse(BaseModel):
    """Structured response from Skeptic agent."""
    concerns: List[str] = Field(..., min_items=1, description="Identified concerns")
    risks: List[str] = Field(..., min_items=1, description="Potential risks")
    reject_recommendation: bool = Field(..., description="Recommends rejection")
    confidence: float = Field(..., ge=0.0, le=1.0)
    key_concern: str = Field(..., description="Primary concern")
    deal_breakers: Optional[List[str]] = Field(default_factory=list, description="Critical issues")


class ModeratorResponse(BaseModel):
    """Structured response from Moderator agent."""
    final_decision: Literal["hire", "conditional_hire", "reject"] = Field(..., description="Final decision")
    decision_rationale: str = Field(..., description="Detailed reasoning")
    confidence: float = Field(..., ge=0.0, le=1.0)
    key_factors: List[str] = Field(..., description="Decisive factors")
    conditions: Optional[List[str]] = Field(default_factory=list, description="Conditions for conditional hire")
    next_steps: List[str] = Field(..., description="Actionable next steps")


class CounterfactualResponse(BaseModel):
    """Schema for counterfactual explanation responses."""
    scenario: str = Field(..., description="What-if scenario description")
    impact: float = Field(..., description="Score impact")
    likelihood: float = Field(..., ge=0.0, le=1.0, description="Likelihood of change")
    actionable: bool = Field(..., description="Whether candidate can action this")
    explanation: str = Field(..., description="Detailed explanation")


class ChainOfThoughtResponse(BaseModel):
    """Schema for reasoning with chain-of-thought."""
    reasoning_steps: List[str] = Field(..., min_items=1, description="Step-by-step reasoning")
    conclusion: str = Field(..., description="Final conclusion")
    confidence: float = Field(..., ge=0.0, le=1.0)
    assumptions: Optional[List[str]] = Field(default_factory=list, description="Key assumptions made")


# Export schemas
__all__ = [
    "AgentResponse",
    "AdvocateResponse", 
    "SkepticResponse",
    "ModeratorResponse",
    "CounterfactualResponse",
    "ChainOfThoughtResponse"
]
