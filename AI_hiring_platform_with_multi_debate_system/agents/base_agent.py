"""
Base agent class and shared utilities for all agents.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from data.schemas import CandidateProfile, JobRequirements


class AgentMessage(BaseModel):
    """Message passed between agents."""
    agent_name: str
    role: str  # evaluator, advocate, skeptic, moderator
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
    """
    Base class for all agents in the system.
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        llm: Optional[Any] = None
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            role: Agent role (evaluator, advocate, skeptic, moderator)
            system_prompt: System prompt defining agent behavior
            llm: LLM instance (Ollama, OpenAI, etc.)
        """
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm = llm
    
    def create_message(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> AgentMessage:
        """
        Create a message from this agent.
        
        Args:
            content: Message content
            metadata: Optional metadata
            
        Returns:
            AgentMessage
        """
        return AgentMessage(
            agent_name=self.name,
            role=self.role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
    
    def format_candidate_info(self, candidate: CandidateProfile) -> str:
        """Format candidate information for prompt."""
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
        """Format job information for prompt."""
        return f"""Job: {job.title}
Department: {job.department}
Level: {job.level}
Required Skills: {', '.join(job.required_skills)}
Preferred Skills: {', '.join(job.preferred_skills or [])}
Min Experience: {job.min_experience_years} years
Required Education: {job.required_education}
Budget: ${job.budget_min:,} - ${job.budget_max:,}
Work Mode: {job.work_mode}"""
    
    def run(self, state: AgentState) -> AgentState:
        """
        Execute agent logic. Override in subclasses.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        raise NotImplementedError("Subclasses must implement run()")


__all__ = ["BaseAgent", "AgentMessage", "AgentState"]
