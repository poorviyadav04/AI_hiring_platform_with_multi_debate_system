"""Multi-agent orchestration workflow."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from hiring_engine.agents.base_agent import AgentState
from hiring_engine.agents.evaluator_agent import EvaluatorAgent
from hiring_engine.agents.advocate_agent import AdvocateAgent
from hiring_engine.agents.skeptic_agent import SkepticAgent
from hiring_engine.agents.moderator_agent import ModeratorAgent
from hiring_engine.schemas.candidate import CandidateProfile
from hiring_engine.schemas.job import JobRequirements
from hiring_engine.schemas.constraints import HiringConstraints

logger = logging.getLogger(__name__)


class MultiAgentWorkflow:
    """
    Orchestrates the multi-agent hiring decision workflow.

    Flow: Evaluator -> Advocate -> Skeptic -> Moderator
    """

    def __init__(
        self,
        constraints: Optional[HiringConstraints] = None,
        llm=None,
    ):
        self.constraints = constraints or HiringConstraints(
            policy_id="POL-DEFAULT", policy_name="Standard Hiring Policy"
        )
        self.llm = llm
        self.evaluator = EvaluatorAgent(constraints=self.constraints, llm=llm)
        self.advocate = AdvocateAgent(llm=llm)
        self.skeptic = SkepticAgent(llm=llm)
        self.moderator = ModeratorAgent(llm=llm)

    async def run(self, candidate: CandidateProfile, job: JobRequirements) -> Dict[str, Any]:
        """Run the multi-agent evaluation workflow."""
        timestamp = datetime.now()
        candidate_id = candidate.candidate_id
        evaluation_id = f"EVAL-{timestamp.strftime('%Y%m%d-%H%M%S')}-{candidate_id}"

        logger.info(
            "Starting evaluation: candidate=%s position=%s id=%s",
            candidate.name, job.title, evaluation_id,
        )

        state = AgentState(candidate=candidate, job=job)

        # Step 1: Evaluator
        logger.info("Step 1: Evaluator scoring...")
        state = await self.evaluator.run(state)
        logger.info("Evaluator complete: score=%.1f", state.scores.get("overall", 0))

        # Step 2: Advocate
        logger.info("Step 2: Advocate building case...")
        state = await self.advocate.run(state)
        logger.info("Advocate complete")

        # Step 3: Skeptic
        logger.info("Step 3: Skeptic analyzing risks...")
        state = await self.skeptic.run(state)
        logger.info("Skeptic complete")

        # Step 4: Moderator
        logger.info("Step 4: Moderator deciding...")
        state = await self.moderator.run(state)
        logger.info("Moderator complete: decision=%s", state.final_decision)

        result = {
            "evaluation_id": evaluation_id,
            "candidate_id": candidate_id,
            "candidate_name": candidate.name,
            "job_id": job.job_id,
            "job_title": job.title,
            "final_decision": state.final_decision,
            "overall_score": state.scores.get("overall", 0),
            "component_scores": {
                "skills": state.scores.get("skills", 0),
                "experience": state.scores.get("experience", 0),
                "education": state.scores.get("education", 0),
            },
            "debate_transcript": [
                {
                    "agent": msg.agent_name,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
                for msg in state.messages
            ],
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            "Evaluation complete: id=%s decision=%s score=%.1f",
            evaluation_id, state.final_decision, state.scores.get("overall", 0),
        )
        return result


__all__ = ["MultiAgentWorkflow"]
