"""Moderator Agent - Synthesizes debate and makes final recommendation."""

import logging
from typing import Optional, Any

from hiring_engine.agents.base_agent import BaseAgent, AgentState

logger = logging.getLogger(__name__)


class ModeratorAgent(BaseAgent):
    """
    Moderator Agent: Synthesizes multi-agent debate into final decision.

    Responsibilities:
    - Review all agent inputs
    - Weight arguments objectively
    - Make final hiring recommendation
    - Provide clear reasoning
    """

    SYSTEM_PROMPT = """You are a Moderator Agent for hiring decisions.

Your role is to SYNTHESIZE the debate and make the FINAL RECOMMENDATION.

You MUST:
1. Review objective evaluation (Evaluator)
2. Consider positive case (Advocate)
3. Acknowledge risks and concerns (Skeptic)
4. Weight all perspectives fairly
5. Make a clear, justified decision
6. Provide actionable next steps

Your decision should:
- Be based on evidence, not emotion
- Account for both data and context
- Consider company needs and constraints
- Be defensible and well-reasoned

Output: hire, conditional_hire, or reject with detailed justification."""

    def __init__(self, llm: Optional[Any] = None):
        """Initialize Moderator Agent."""
        super().__init__(
            name="Moderator",
            role="moderator",
            system_prompt=self.SYSTEM_PROMPT,
            llm=llm,
        )

    async def run(self, state: AgentState) -> AgentState:
        """Synthesize debate and make final recommendation."""
        candidate = state.candidate
        job = state.job
        scores = state.scores

        # Extract key points from each agent
        evaluator_msg = next((m for m in state.messages if m.role == "evaluator"), None)
        advocate_msg = next((m for m in state.messages if m.role == "advocate"), None)
        skeptic_msg = next((m for m in state.messages if m.role == "skeptic"), None)

        if self.llm:
            decision, reasoning = await self._make_decision_llm(
                candidate, job, scores,
                evaluator_msg, advocate_msg, skeptic_msg,
            )
        else:
            decision_type, reasoning_text = self._make_decision(
                candidate, job, scores,
                evaluator_msg, advocate_msg, skeptic_msg,
            )

            # Add consistency check logic before final decision
            overall_score = scores.get('overall', 0)

            # Check consistency with past decisions
            try:
                from hiring_engine.rag.memory_query import get_memory_helper
                memory = get_memory_helper()
                consistency_check = memory.check_consistency(
                    candidate, job, overall_score, decision_type,
                )

                if consistency_check['similar_cases'] > 0:
                    reasoning_text += "\nCONSISTENCY CHECK:\n"
                    if consistency_check['is_consistent']:
                        reasoning_text += f"Decision is CONSISTENT with {consistency_check['similar_cases']} similar past case(s).\n"
                    else:
                        reasoning_text += f"INCONSISTENCY DETECTED with {consistency_check['similar_cases']} similar past case(s):\n"
                        for flag in consistency_check['flags']:
                            reasoning_text += f"  - {flag}\n"
                        reasoning_text += "\nThese inconsistencies should be carefully reviewed.\n"
            except Exception:
                # If memory not available, continue without it
                logger.debug("Memory helper not available for moderator agent")

            decision = decision_type
            reasoning = reasoning_text

        # Update state
        state.final_decision = decision
        state.reasoning = reasoning

        # Add final message
        message = self.create_message(
            content=reasoning,
            metadata={'decision': decision},
        )
        state.messages.append(message)

        logger.info("Moderator complete: decision=%s for candidate=%s", decision, candidate.name)
        return state

    async def _make_decision_llm(self, candidate, job, scores, evaluator_msg, advocate_msg, skeptic_msg):
        """Make decision using LLM for natural language synthesis."""
        context = f"""Candidate: {candidate.name}
Position: {job.title} ({job.level})

OVERALL SCORE: {scores.get('overall', 0):.1f}/100

=== EVALUATOR'S ASSESSMENT ===
{evaluator_msg.content[:500] if evaluator_msg else 'N/A'}
...

=== ADVOCATE'S ARGUMENT ===
{advocate_msg.content[:400] if advocate_msg else 'N/A'}
...

=== SKEPTIC'S CONCERNS ===
{skeptic_msg.content[:400] if skeptic_msg else 'N/A'}
...

TASK: Synthesize all perspectives and make a final hiring decision. Choose ONE of:
- "hire" (if strong fit, score 85+, minimal risks)
- "conditional_hire" (if acceptable with conditions, score 65-84)
- "reject" (if poor fit, score <65, or major concerns)

Provide clear reasoning balancing all viewpoints. Start your response with the decision in ALL CAPS, then explain."""

        synthesis = await self.llm.generate(
            prompt=context,
            system=self.SYSTEM_PROMPT,
            temperature=0.5,
            max_tokens=1000,
        )

        # Extract decision from response
        decision = "conditional_hire"  # Default
        if "HIRE" in synthesis[:50].upper() and "CONDITIONAL" not in synthesis[:50].upper():
            decision = "hire"
        elif "REJECT" in synthesis[:50].upper():
            decision = "reject"

        return decision, synthesis

    def _make_decision(self, candidate, job, scores, evaluator_msg, advocate_msg, skeptic_msg):
        """Make final hiring decision."""

        overall_score = scores.get('overall', 0)

        # Get validation result
        validation = None
        if evaluator_msg and 'validation' in evaluator_msg.metadata:
            validation = evaluator_msg.metadata['validation']

        decision_text = f"""FINAL HIRING DECISION: {candidate.name.upper()}
{'=' * 70}

SYNTHESIS OF MULTI-AGENT DEBATE:

1. EVALUATOR'S ASSESSMENT:
   Overall Score: {overall_score:.1f}/100
   Skills: {scores.get('skills', 0):.0f} | Experience: {scores.get('experience', 0):.0f} | Education: {scores.get('education', 0):.0f} | Interviews: {scores.get('interviews', 0):.0f}
"""

        if validation:
            decision_text += f"   Constraint Compliance: {validation['compliance_rate']*100:.0f}%\n"
            if validation['violations']:
                decision_text += f"   Violations: {len(validation['violations'])}\n"
            if validation['warnings']:
                decision_text += f"   Warnings: {len(validation['warnings'])}\n"

        decision_text += "\n2. ADVOCATE'S PERSPECTIVE:\n"
        decision_text += "   Highlights candidate strengths and potential\n"
        decision_text += "   Emphasizes growth opportunities and value-add\n"
        decision_text += "   Proposes mitigation for gaps through training\n"

        decision_text += "\n3. SKEPTIC'S CONCERNS:\n"
        decision_text += "   Identifies risks and weaknesses\n"
        decision_text += "   Challenges assumptions about candidate readiness\n"
        decision_text += "   Questions opportunity cost vs other candidates\n"

        # Decision logic
        decision_text += f"\nDECISION FRAMEWORK:\n"

        # Automatic reject conditions
        if overall_score < 50:
            decision = "reject"
            decision_text += f"  Score ({overall_score:.0f}) far below acceptable threshold\n"
            decision_text += f"  Fundamental fit issues cannot be reconciled\n"

        elif validation and validation['compliance_rate'] < 0.5:
            decision = "reject"
            decision_text += f"  Multiple critical policy violations\n"
            decision_text += f"  Compliance ({validation['compliance_rate']*100:.0f}%) too low\n"

        # Strong hire
        elif overall_score >= 85 and (not validation or validation['all_compliant']):
            decision = "hire"
            decision_text += f"  Strong score ({overall_score:.0f}) indicates excellent fit\n"
            decision_text += f"  All constraints satisfied\n"
            decision_text += f"  Minimal risks, high upside\n"

        # Hire with conditions
        elif overall_score >= 75 or (overall_score >= 65 and validation and validation['all_compliant']):
            decision = "conditional_hire"
            decision_text += f"  Score ({overall_score:.0f}) meets threshold\n"
            decision_text += f"  Some concerns but manageable with mitigation\n"
            decision_text += f"  Requires specific conditions before offer\n"

        # Conditional or reject
        elif overall_score >= 65:
            if validation and validation['compliance_rate'] >= 0.66:
                decision = "conditional_hire"
                decision_text += f"  Borderline score ({overall_score:.0f})\n"
                decision_text += f"  Multiple gaps require addressed\n"
                decision_text += f"  Proceed only if no better candidates available\n"
            else:
                decision = "reject"
                decision_text += f"  Score ({overall_score:.0f}) + compliance issues\n"
                decision_text += f"  Too many risks for moderate upside\n"

        # Reject
        else:
            decision = "reject"
            decision_text += f"  Score ({overall_score:.0f}) below hiring threshold\n"
            decision_text += f"  Risks outweigh potential benefits\n"

        decision_text += f"\n{'=' * 70}\n"
        decision_text += f"FINAL DECISION: {decision.upper().replace('_', ' ')}\n"
        decision_text += f"{'=' * 70}\n\n"

        # Specific reasoning
        if decision == "hire":
            decision_text += f"RATIONALE:\n"
            decision_text += f"After weighing all perspectives, I recommend we EXTEND AN OFFER to {candidate.name}.\n\n"
            decision_text += f"This candidate demonstrates:\n"
            decision_text += f"- Strong objective metrics across all dimensions\n"
            decision_text += f"- Minimal risk profile with clear upside potential\n"
            decision_text += f"- Alignment with role requirements and company values\n\n"
            decision_text += f"NEXT STEPS:\n"
            decision_text += f"1. Prepare offer letter at ${candidate.salary_expectation:,}\n"
            decision_text += f"2. Schedule final conversation with hiring manager\n"
            decision_text += f"3. Begin reference checks\n"
            decision_text += f"4. Target start date within 2-4 weeks\n"

        elif decision == "conditional_hire":
            decision_text += f"RATIONALE:\n"
            decision_text += f"I recommend CONDITIONAL APPROVAL to hire {candidate.name}.\n\n"
            decision_text += f"While this candidate shows promise, specific conditions must be met:\n\n"

            # Determine conditions
            conditions = []
            if scores.get('skills', 0) < 75:
                conditions.append("Commit to 30-60-90 day skill development plan")
            if candidate.salary_expectation > job.budget_max:
                conditions.append(f"Salary negotiation to ${job.budget_max:,} or below")
            if validation and validation['warnings']:
                conditions.append("VP approval for policy exceptions")
            if scores.get('interviews', 0) < 75:
                conditions.append("Additional technical or behavioral interview")

            if not conditions:
                conditions = [
                    "Successful reference checks (3+ professional references)",
                    "Background check clearance",
                    "Final approval from hiring manager",
                ]

            decision_text += f"CONDITIONS:\n"
            for i, condition in enumerate(conditions, 1):
                decision_text += f"{i}. {condition}\n"

            decision_text += f"\nONLY proceed with offer if ALL conditions are satisfied.\n"

        else:  # reject
            decision_text += f"RATIONALE:\n"
            decision_text += f"I recommend we DO NOT EXTEND AN OFFER to {candidate.name}.\n\n"
            decision_text += f"After careful consideration:\n"
            decision_text += f"- Objective metrics indicate poor fit for role requirements\n"
            decision_text += f"- Risks and gaps are too significant to mitigate effectively\n"
            decision_text += f"- Better candidates likely available in market\n\n"
            decision_text += f"NEXT STEPS:\n"
            decision_text += f"1. Send professional rejection notice\n"
            decision_text += f"2. Continue recruiting efforts\n"
            decision_text += f"3. Review job requirements if pattern of rejections\n"
            decision_text += f"4. Consider expanding candidate sourcing channels\n"

        decision_text += f"\n{'=' * 70}\n"
        decision_text += "End of Decision Synthesis\n"

        return decision, decision_text


__all__ = ["ModeratorAgent"]
