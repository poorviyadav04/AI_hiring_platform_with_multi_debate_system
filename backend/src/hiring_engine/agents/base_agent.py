"""Base agent class and shared utilities."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

from hiring_engine.schemas.candidate import CandidateProfile
from hiring_engine.schemas.job import JobRequirements

logger = logging.getLogger(__name__)


class AgentMessage(BaseModel):
    """Message passed between agents."""
    agent_name: str
    role: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class AgentState(BaseModel):
    """Shared state for multi-agent workflow."""
    candidate: CandidateProfile
    job: JobRequirements
    messages: List[AgentMessage] = []
    scores: Dict[str, float] = {}
    final_decision: Optional[str] = None
    reasoning: Optional[str] = None


class BaseAgent:
    """Base class for all agents."""

    def __init__(self, name: str, role: str, system_prompt: str, llm: Optional[Any] = None):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm = llm

    def create_message(self, content: str, metadata: Optional[Dict] = None) -> AgentMessage:
        return AgentMessage(
            agent_name=self.name,
            role=self.role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )

    def format_candidate_info(self, candidate: CandidateProfile) -> str:
        return f"""Candidate: {candidate.name} (ID: {candidate.candidate_id})
Education: {candidate.education}
Experience: {candidate.experience_years} years
Skills: {', '.join(candidate.skills)}
Work Preference: {candidate.work_preference}
Salary Expectation: ${candidate.salary_expectation:,}
Technical Score: {candidate.technical_interview_score or 'N/A'}
Behavioral Score: {candidate.behavioral_interview_score or 'N/A'}
Coding Challenge: {candidate.coding_challenge_score or 'N/A'}"""

    def format_job_info(self, job: JobRequirements) -> str:
        return f"""Job: {job.title}
Department: {job.department}
Level: {job.level}
Required Skills: {', '.join(job.required_skills)}
Preferred Skills: {', '.join(job.preferred_skills or [])}
Min Experience: {job.min_experience_years} years
Required Education: {job.required_education}
Budget: ${job.budget_min:,} - ${job.budget_max:,}
Work Mode: {job.work_mode}"""

    async def run(self, state: AgentState) -> AgentState:
        raise NotImplementedError("Subclasses must implement run()")


__all__ = ["BaseAgent", "AgentMessage", "AgentState"]
