"""
Advocate Agent - Makes the case FOR hiring the candidate.
"""

from typing import Optional, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent, AgentState


class AdvocateAgent(BaseAgent):
    """
    Advocate Agent: Makes the strongest case FOR hiring the candidate.
    
    Responsibilities:
    - Highlight candidate strengths
    - Emphasize potential and growth
    - Counter potential objections
    - Show positive outlook
    """
    
    SYSTEM_PROMPT = """You are an Advocate Agent for hiring decisions.

Your role is to make the STRONGEST CASE for hiring this candidate.

You MUST:
1. Highlight all strengths and positive attributes
2. Emphasize potential for growth and learning
3. Explain how gaps can be addressed (training, mentorship)
4. Compare favorably to market standards
5. Focus on culture fit and soft skills
6. Use optimistic but realistic language

You may:
- Acknowledge weaknesses but frame them as opportunities
- Reference similar successful hires
- Emphasize unique qualities

Be persuasive but honest. Don't fabricate qualifications."""
    
    def __init__(self, llm: Optional[Any] = None):
        """Initialize Advocate Agent."""
        super().__init__(
            name="Advocate",
            role="advocate",
            system_prompt=self.SYSTEM_PROMPT,
            llm=llm
        )
    
    def run(self, state: AgentState) -> AgentState:
        """
        Make the case FOR hiring the candidate using LLM.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with advocacy
        """
        candidate = state.candidate
        job = state.job
        scores = state.scores
        
        # Build advocacy argument
        if self.llm:
            # LLM-powered natural language advocacy
            advocacy = self._build_advocacy_llm(candidate, job, scores)
        else:
            # Fallback to deterministic template
            advocacy = self._build_advocacy(candidate, job, scores)
        
        # Add message to state
        message = self.create_message(content=advocacy)
        state.messages.append(message)
        
        return state
    
    def _build_advocacy_llm(self, candidate, job, scores) -> str:
        """Build advocacy using LLM for natural language."""
        from utils.llm_client import get_llm_client
        
        llm = get_llm_client()
        
        # Build context for LLM
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

TASK: Make a compelling, persuasive case FOR hiring this candidate. Highlight strengths, frame any gaps as growth opportunities, and explain why they're a strong fit. Be optimistic but honest."""

        # Generate advocacy
        advocacy = llm.generate(
            prompt=context,
            system=self.SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=800
        )
        
        return advocacy
    
    def _build_advocacy(self, candidate, job, scores) -> str:
        """Build advocacy argument."""
        
        advocacy = f"""ADVOCACY: CASE FOR HIRING {candidate.name.upper()}
{'=' * 70}

EXECUTIVE SUMMARY:
I strongly advocate for hiring {candidate.name} for the {job.title} position.
This candidate demonstrates significant strengths that align well with our needs.

KEY STRENGTHS:

"""
        
        # Highlight skills
        matched_skills = [s for s in candidate.skills if s in job.required_skills]
        if matched_skills:
            advocacy += f"1. TECHNICAL PROFICIENCY\n"
            advocacy += f"   ✓ Possesses {len(matched_skills)} of {len(job.required_skills)} required skills\n"
            advocacy += f"   ✓ Core competencies: {', '.join(matched_skills[:5])}\n"
            
            # Find additional valuable skills
            extra_skills = [s for s in candidate.skills if s not in job.required_skills]
            if extra_skills:
                advocacy += f"   ✓ Brings bonus expertise: {', '.join(extra_skills[:3])}\n"
            advocacy += "\n"
        
        # Experience perspective
        advocacy += f"2. EXPERIENCE & GROWTH POTENTIAL\n"
        if candidate.experience_years >= job.min_experience_years:
            advocacy += f"   ✓ Meets experience requirement ({candidate.experience_years} years)\n"
            advocacy += f"   ✓ Proven track record in the industry\n"
        else:
            gap = job.min_experience_years - candidate.experience_years
            advocacy += f"   ✓ Strong foundation with {candidate.experience_years} years of hands-on experience\n"
            advocacy += f"   ✓ Quick learner - the {gap:.1f} year gap can be bridged with mentorship\n"
            advocacy += f"   ✓ Fresh perspective and hunger to prove themselves\n"
        advocacy += "\n"
        
        # Interview scores
        if scores.get('interviews', 0) >= 70:
            advocacy += f"3. INTERVIEW PERFORMANCE\n"
            advocacy += f"   ✓ Strong interview scores ({scores['interviews']:.0f}/100)\n"
            if candidate.technical_interview_score and candidate.technical_interview_score >= 75:
                advocacy += f"   ✓ Technical interview: {candidate.technical_interview_score:.0f}/100 - Excellent problem-solving\n"
            if candidate.behavioral_interview_score and candidate.behavioral_interview_score >= 75:
                advocacy += f"   ✓ Behavioral interview: {candidate.behavioral_interview_score:.0f}/100 - Great culture fit\n"
            advocacy += "\n"
        
        # Budget fit
        if candidate.salary_expectation <= job.budget_max:
            advocacy += f"4. BUDGET ALIGNMENT\n"
            advocacy += f"   ✓ Salary expectation (${candidate.salary_expectation:,}) within budget\n"
            if candidate.salary_expectation < job.budget_max * 0.9:
                margin = job.budget_max - candidate.salary_expectation
                advocacy += f"   ✓ Provides ${margin:,} budget cushion for bonuses/benefits\n"
            advocacy += "\n"
        
        # Overall score interpretation
        overall = scores.get('overall', 0)
        advocacy += f"5. HOLISTIC ASSESSMENT\n"
        if overall >= 85:
            advocacy += f"   ✓ Overall score of {overall:.0f}/100 - Top tier candidate\n"
            advocacy += f"   ✓ Rare find in current market conditions\n"
        elif overall >= 75:
            advocacy += f"   ✓ Overall score of {overall:.0f}/100 - Strong hire\n"
            advocacy += f"   ✓ Well-rounded candidate with solid fundamentals\n"
        elif overall >= 65:
            advocacy += f"   ✓ Overall score of {overall:.0f}/100 - Good potential\n"
            advocacy += f"   ✓ With proper onboarding, can exceed expectations\n"
        else:
            advocacy += f"   • Score of {overall:.0f}/100 - Diamond in the rough\n"
            advocacy += f"   ✓ Numbers don't tell the whole story - consider intangibles\n"
        
        advocacy += "\nWHY THIS CANDIDATE STANDS OUT:\n"
        advocacy += f"• {candidate.work_preference.capitalize()} preference aligns with our {job.work_mode} model\n"
        advocacy += f"• Educational background ({candidate.education}) provides strong foundation\n"
        advocacy += f"• Diverse skill set brings cross-functional value\n"
        
        advocacy += f"\nRISK MITIGATION:\n"
        advocacy += "• Any skill gaps can be addressed through our robust training program\n"
        advocacy += "• 90-day onboarding plan will ensure rapid productivity\n"
        advocacy += "• Regular check-ins and mentorship will accelerate growth\n"
        
        advocacy += f"\nRECOMMENDATION:\n"
        advocacy += f"Based on the comprehensive evaluation, I recommend we PROCEED with an offer to {candidate.name}.\n"
        advocacy += f"This candidate represents a strong value proposition with clear upside potential.\n"
        
        # Query memory for similar past hires  
        memory_context = ""
        try:
            from tools.memory_query import get_memory_helper
            memory = get_memory_helper()
            similar_hires = memory.find_similar_hires(candidate, job, top_k=3)
            
            if similar_hires:
                memory_context = "\n📚 PAST EVIDENCE:\n"
                memory_context += f"We have hired {len(similar_hires)} similar candidate(s) before:\n"
                for i, hire in enumerate(similar_hires, 1):
                    memory_context += f"  {i}. {hire['candidate_name']} for {hire['job_title']} "
                    memory_context += f"(Score: {hire['score']:.1f}, {hire['timestamp']})\n"
                memory_context += "This demonstrates our organization values similar profiles!\n"
                advocacy += f"\n{memory_context}"
        except Exception:
            # If memory not available, continue without it
            pass
        
        advocacy += f"\n{'=' * 70}\n"
        
        return advocacy


__all__ = ["AdvocateAgent"]

