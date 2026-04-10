"""Skeptic Agent - Challenges the hiring decision with critical analysis."""

import logging
from typing import Optional, Any

from hiring_engine.agents.base_agent import BaseAgent, AgentState

logger = logging.getLogger(__name__)


class SkepticAgent(BaseAgent):
    """
    Skeptic Agent: Plays devil's advocate and identifies risks.

    Responsibilities:
    - Identify weaknesses and gaps
    - Challenge assumptions
    - Highlight risks and concerns
    - Ensure thorough vetting
    """

    SYSTEM_PROMPT = """You are a Skeptic Agent for hiring decisions.

Your role is to identify RISKS, GAPS, and CONCERNS about hiring this candidate.

You MUST:
1. Critically examine all weaknesses
2. Identify potential red flags
3. Challenge optimistic assumptions
4. Consider worst-case scenarios
5. Question whether gaps can realistically be filled
6. Compare to ideal candidate profile

You should:
- Be critical but fair
- Use data to support concerns
- Consider opportunity cost (could we find better?)
- Think about retention risk

Be skeptical but constructive. Help us make a better decision by stress-testing it."""

    def __init__(self, llm: Optional[Any] = None):
        """Initialize Skeptic Agent."""
        super().__init__(
            name="Skeptic",
            role="skeptic",
            system_prompt=self.SYSTEM_PROMPT,
            llm=llm,
        )

    async def run(self, state: AgentState) -> AgentState:
        """Challenge the hiring decision with critical analysis."""
        candidate = state.candidate
        job = state.job
        scores = state.scores

        # Find evaluator's validation results
        evaluator_msg = next(
            (m for m in state.messages if m.role == "evaluator"),
            None,
        )

        validation = None
        if evaluator_msg and 'validation' in evaluator_msg.metadata:
            validation = evaluator_msg.metadata['validation']

        if self.llm:
            critique = await self._build_critique_llm(candidate, job, scores, validation)
        else:
            critique = self._build_critique(candidate, job, scores, validation)

        message = self.create_message(content=critique)
        state.messages.append(message)

        logger.info("Skeptic complete for candidate=%s", candidate.name)
        return state

    async def _build_critique_llm(self, candidate, job, scores, validation) -> str:
        """Build critique using LLM for natural language."""
        context = f"""Candidate: {candidate.name}
Position: {job.title} ({job.level})

EVALUATION SCORES:
- Overall: {scores.get('overall', 0):.1f}/100
- Skills: {scores.get('skills', 0):.0f}/100
- Experience: {scores.get('experience', 0):.0f}/100
- Education: {scores.get('education', 0):.0f}/100
- Interviews: {scores.get('interviews', 0):.0f}/100

CANDIDATE DETAILS:
{self.format_candidate_info(candidate)}

JOB REQUIREMENTS:
{self.format_job_info(job)}
"""

        if validation:
            context += f"\nCONSTRAINT VALIDATION:\n"
            context += f"- Compliant: {validation['all_compliant']}\n"
            context += f"- Violations: {len(validation['violations'])}\n"
            if validation['violations']:
                context += f"  Issues: {', '.join(validation['violations'][:3])}\n"

        context += "\nTASK: Identify risks, concerns, and potential problems with hiring this candidate. Play devil's advocate. Be critical but fair. Point out gaps, challenges, and opportunity costs."

        critique = await self.llm.generate(
            prompt=context,
            system=self.SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=800,
        )

        return critique

    def _build_critique(self, candidate, job, scores, validation) -> str:
        """Build critical analysis."""

        critique = f"""CRITICAL ANALYSIS: RISKS & CONCERNS FOR {candidate.name.upper()}
{'=' * 70}

EXECUTIVE SUMMARY:
While this candidate shows some promise, I must highlight several concerns
that warrant careful consideration before extending an offer.

IDENTIFIED CONCERNS:

"""

        concern_count = 0

        # Skill gaps
        missing_skills = []
        for req_skill in job.required_skills:
            if req_skill not in candidate.skills:
                missing_skills.append(req_skill)

        if missing_skills:
            concern_count += 1
            critique += f"{concern_count}. CRITICAL SKILL GAPS\n"
            critique += f"   Missing {len(missing_skills)} required skills: {', '.join(missing_skills)}\n"
            critique += f"   - These are REQUIRED, not preferred\n"
            critique += f"   - Learning curve will delay productivity\n"
            critique += f"   - Onboarding cost and time investment needed\n"
            critique += f"   - Risk: May struggle with immediate responsibilities\n\n"

        # Experience concerns
        if candidate.experience_years < job.min_experience_years:
            concern_count += 1
            gap = job.min_experience_years - candidate.experience_years
            critique += f"{concern_count}. EXPERIENCE DEFICIT\n"
            critique += f"   {gap:.1f} years below minimum requirement\n"
            critique += f"   - May lack seasoned judgment for {job.level} role\n"
            critique += f"   - Increased supervision needed\n"
            critique += f"   - Risk: May be overwhelmed by seniority expectations\n\n"

        elif candidate.experience_years > job.min_experience_years * 2:
            concern_count += 1
            critique += f"{concern_count}. OVERQUALIFICATION RISK\n"
            critique += f"   Significantly overqualified ({candidate.experience_years} years for {job.min_experience_years} year role)\n"
            critique += f"   - May become bored quickly\n"
            critique += f"   - Flight risk within 6-12 months\n"
            critique += f"   - Likely using this as a stepping stone\n"
            critique += f"   - Risk: High turnover and wasted hiring investment\n\n"

        # Budget concerns
        if validation and not validation['detailed_checks']['budget']['strictly_compliant']:
            concern_count += 1
            budget_check = validation['detailed_checks']['budget']
            critique += f"{concern_count}. BUDGET CONCERNS\n"
            critique += f"   {budget_check['status'].upper()}\n"
            critique += f"   - Salary: ${candidate.salary_expectation:,} vs Budget: ${job.budget_max:,}\n"
            if budget_check['status'] == 'exceeds_tolerance':
                critique += f"   - Cannot afford without budget adjustment\n"
            critique += f"   - Risk: Budget overrun or failed negotiation\n\n"

        # Score concerns
        overall = scores.get('overall', 0)
        if overall < 75:
            concern_count += 1
            critique += f"{concern_count}. BELOW THRESHOLD PERFORMANCE\n"
            critique += f"   Overall score: {overall:.0f}/100 (below 'Hire' threshold of 75)\n"

            if scores.get('skills', 0) < 70:
                critique += f"   - Skills score: {scores['skills']:.0f}/100 - Weak match\n"
            if scores.get('experience', 0) < 70:
                critique += f"   - Experience score: {scores['experience']:.0f}/100 - Questionable fit\n"
            if scores.get('interviews', 0) < 70:
                critique += f"   - Interview score: {scores['interviews']:.0f}/100 - Mediocre performance\n"

            critique += f"   - Risk: May not meet job expectations\n\n"

        # Interview red flags
        if candidate.technical_interview_score and candidate.technical_interview_score < 65:
            concern_count += 1
            critique += f"{concern_count}. TECHNICAL COMPETENCY QUESTIONS\n"
            critique += f"   Technical interview: {candidate.technical_interview_score:.0f}/100\n"
            critique += f"   - Below passing threshold\n"
            critique += f"   - Struggled with core concepts\n"
            critique += f"   - Risk: Cannot handle technical challenges\n\n"

        # Constraint violations
        if validation and validation['violations']:
            concern_count += 1
            critique += f"{concern_count}. POLICY VIOLATIONS\n"
            for v in validation['violations']:
                critique += f"   {v}\n"
            critique += f"   - Requires waiver or exception\n"
            critique += f"   - Sets precedent for future hires\n"
            critique += f"   - Risk: Compliance and consistency issues\n\n"

        # If no major concerns found
        if concern_count == 0:
            critique += "1. OPPORTUNITY COST\n"
            critique += "   - While candidate meets minimums, could we find better?\n"
            critique += "   - Market conditions may yield stronger candidates\n"
            critique += "   - Risk: Settling for 'good enough' vs 'great'\n\n"
            concern_count = 1

        critique += f"RISK ASSESSMENT:\n"
        if concern_count >= 4:
            critique += "  HIGH RISK - Multiple serious concerns identified\n"
            critique += "     Consider alternative candidates\n"
        elif concern_count >= 2:
            critique += "  MODERATE RISK - Several concerns need addressing\n"
            critique += "     Proceed with caution and mitigation plan\n"
        else:
            critique += "  LOW-MODERATE RISK - Minimal concerns\n"
            critique += "     Concerns are manageable with proper support\n"

        critique += f"\nQUESTIONS TO CONSIDER:\n"
        critique += "- Can we realistically close the skill gaps within 3-6 months?\n"
        critique += "- Do we have mentorship resources to support this hire?\n"
        critique += "- Are there stronger candidates in our pipeline?\n"
        critique += "- What's our risk tolerance for this role?\n"
        critique += "- Have we exhausted our recruiting channels?\n"

        critique += f"\nRECOMMENDATION:\n"
        if concern_count >= 3:
            critique += f"Exercise CAUTION. Consider passing or requiring additional\n"
            critique += f"evaluation steps before making an offer to {candidate.name}.\n"
        critique += f"\nCONCLUSION:\n"
        critique += f"While {candidate.name} has some positive qualities, the identified gaps and risks "
        critique += f"require careful consideration before proceeding.\n"

        # Query memory for similar past rejections
        try:
            from hiring_engine.rag.memory_query import get_memory_helper
            memory = get_memory_helper()
            similar_rejections = memory.find_similar_rejections(candidate, job, top_k=3)

            if similar_rejections:
                critique += "\nHISTORICAL PRECEDENT:\n"
                critique += f"We have rejected {len(similar_rejections)} similar candidate(s) before:\n"
                for i, rejection in enumerate(similar_rejections, 1):
                    critique += f"  {i}. {rejection['candidate_name']} for {rejection['job_title']} "
                    critique += f"(Score: {rejection['score']:.1f}, {rejection['timestamp']})\n"
                critique += "These past decisions support a cautious approach.\n"
        except Exception:
            # If memory not available, continue without it
            logger.debug("Memory helper not available for skeptic agent")

        critique += f"\n{'=' * 70}\n"

        return critique


__all__ = ["SkepticAgent"]
