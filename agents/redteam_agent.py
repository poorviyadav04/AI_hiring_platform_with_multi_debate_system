"""
Red Team Agent - Adversarial testing and bias detection.

This agent challenges hiring decisions to ensure fairness, robustness,
and identify potential biases or edge cases.
"""

from typing import Optional, Any, List, Dict
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent, AgentState
from tools.counterfactuals import CounterfactualGenerator


class RedTeamAgent(BaseAgent):
    """
    Red Team Agent: Challenges decisions through adversarial testing.
    
    Responsibilities:
    - Detect potential biases
    - Identify edge cases
    - Challenge weak reasoning
    - Test decision boundaries
    - Ensure fairness and consistency
    """
    
    SYSTEM_PROMPT = """You are a Red Team Agent for hiring decisions.

Your role is to CHALLENGE the hiring decision through adversarial testing.

You MUST:
1. Question the logic and reasoning
2. Identify potential biases (age, gender, background)
3. Test edge cases and boundary conditions
4. Challenge weak or inconsistent arguments
5. Ensure fairness across all candidates
6. Point out any red flags in the decision

You may:
- Play devil's advocate aggressively
- Highlight contradictions in the debate
- Surface implicit biases
- Test decision robustness

Be rigorous but constructive. The goal is to make decisions STRONGER, not to reject all candidates."""
    
    def __init__(self, llm: Optional[Any] = None):
        """Initialize Red Team Agent."""
        super().__init__(
            name="RedTeam",
            role="redteam",
            system_prompt=self.SYSTEM_PROMPT,
            llm=llm
        )
        self.cf_generator = CounterfactualGenerator()
    
    def run(self, state: AgentState) -> AgentState:
        """
        Challenge the hiring decision with adversarial testing.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with red team analysis
        """
        candidate = state.candidate
        job = state.job
        scores = state.scores
        
        # Get all previous messages
        evaluator_msg = next((m for m in state.messages if m.role == "evaluator"), None)
        advocate_msg = next((m for m in state.messages if m.role == "advocate"), None)
        skeptic_msg = next((m for m in state.messages if m.role == "skeptic"), None)
        moderator_msg = next((m for m in state.messages if m.role == "moderator"), None)
        
        # Build red team analysis
        if self.llm:
            analysis = self._build_analysis_llm(
                candidate, job, scores,
                evaluator_msg, advocate_msg, skeptic_msg, moderator_msg
            )
        else:
            analysis = self._build_analysis(
                candidate, job, scores,
                evaluator_msg, advocate_msg, skeptic_msg, moderator_msg
            )
        
        # Add message to state
        message = self.create_message(
            content=analysis,
            metadata={'challenges_found': len(self._extract_challenges(analysis))}
        )
        state.messages.append(message)
        
        return state
    
    def _build_analysis_llm(self, candidate, job, scores, evaluator_msg, advocate_msg, skeptic_msg, moderator_msg) -> str:
        """Build analysis using LLM."""
        from utils.llm_client import get_llm_client
        
        llm = get_llm_client()
        
        # Build context
        context = f"""Candidate: {candidate.name}
Position: {job.title} ({job.level})

OVERALL SCORE: {scores.get('overall', 0):.1f}/100
FINAL DECISION: {moderator_msg.metadata.get('decision', 'unknown') if moderator_msg else 'unknown'}

=== EVALUATOR'S ASSESSMENT ===
{evaluator_msg.content[:400] if evaluator_msg else 'N/A'}

=== ADVOCATE'S ARGUMENT ===
{advocate_msg.content[:400] if advocate_msg else 'N/A'}

=== SKEPTIC'S CONCERNS ===
{skeptic_msg.content[:400] if skeptic_msg else 'N/A'}

=== MODERATOR'S DECISION ===
{moderator_msg.content[:400] if moderator_msg else 'N/A'}

TASK: As a Red Team agent, challenge this decision. Look for:
1. Potential biases (age, background, gender indicators in name/education)
2. Inconsistencies between agents
3. Edge cases not considered
4. Weak reasoning or assumptions
5. Fairness concerns

Be adversarial but constructive."""

        # Generate analysis
        analysis = llm.generate(
            prompt=context,
            system=self.SYSTEM_PROMPT,
            temperature=0.6,
            max_tokens=1000
        )
        
        # If LLM returns fallback message, use deterministic analysis instead
        if "[Ollama not available" in analysis or "FALLBACK MODE" in analysis:
            fallback_banner = analysis  # Keep the LLM fallback banner
            deterministic = self._build_analysis(
                candidate, job, scores,
                evaluator_msg, advocate_msg, skeptic_msg, moderator_msg
            )
            return fallback_banner + "\n\n" + deterministic
        
        return analysis
    
    def _build_analysis(self, candidate, job, scores, evaluator_msg, advocate_msg, skeptic_msg, moderator_msg) -> str:
        """Build deterministic red team analysis."""
        
        analysis = f"""RED TEAM ANALYSIS: ADVERSARIAL CHALLENGE
{'=' * 70}

DECISION UNDER REVIEW:
Candidate: {candidate.name}
Position: {job.title} ({job.level})
Overall Score: {scores.get('overall', 0):.1f}/100
Decision: {moderator_msg.metadata.get('decision', 'unknown').upper() if moderator_msg else 'UNKNOWN'}

ADVERSARIAL CHALLENGES:

"""
        
        challenges = []
        
        # Challenge 1: Bias Detection
        bias_check = self._detect_bias(candidate, job, scores)
        if bias_check:
            challenges.append(f"⚠️  BIAS ALERT: {bias_check}")
        
        # Challenge 2: Score Boundary Testing
        boundary_check = self._test_boundaries(candidate, job, scores)
        if boundary_check:
            challenges.append(f"🔍 BOUNDARY CASE: {boundary_check}")
        
        # Challenge 3: Consistency Check
        consistency_check = self._check_consistency(scores, moderator_msg)
        if consistency_check:
            challenges.append(f"❌ INCONSISTENCY: {consistency_check}")
        
        # Challenge 4: Edge Case Identification
        edge_cases = self._identify_edge_cases(candidate, job)
        if edge_cases:
            challenges.append(f"⚡ EDGE CASE: {edge_cases}")
        
        # Challenge 5: Fairness Check
        fairness = self._check_fairness(candidate, job, scores)
        if fairness:
            challenges.append(f"⚖️  FAIRNESS CONCERN: {fairness}")
        
        if challenges:
            for i, challenge in enumerate(challenges, 1):
                analysis += f"{i}. {challenge}\n\n"
        else:
            analysis += "✅ No significant challenges identified.\n"
            analysis += "   Decision appears robust and fair.\n\n"
        
        # Counterfactual sensitivity
        analysis += self._sensitivity_test(candidate, job, scores)
        
        # Final verdict
        analysis += f"\nRED TEAM VERDICT:\n"
        if len(challenges) == 0:
            analysis += "✅ DECISION APPROVED - No critical issues found\n"
        elif len(challenges) <= 2:
            analysis += "⚠️  DECISION CONDITIONAL - Minor concerns identified, proceed with caution\n"
        else:
            analysis += "❌ DECISION CHALLENGED - Multiple concerns require review\n"
        
        analysis += f"\n{'=' * 70}\n"
        
        return analysis
    
    def _detect_bias(self, candidate, job, scores) -> Optional[str]:
        """Detect potential biases."""
        issues = []
        
        # Check for education bias
        if scores.get('education', 0) < 50 and candidate.education in ["Bootcamp", "High School"]:
            issues.append("Non-traditional education heavily penalized")
        
        # Check for experience bias (ageism)
        if candidate.experience_years > job.min_experience_years * 2:
            if scores.get('experience', 0) < 95:
                issues.append("Overqualified candidate penalized (potential age discrimination)")
        
        # Check for salary bias
        if candidate.salary_expectation < job.budget_min * 0.8:
            issues.append("Low salary expectation might indicate undervaluing (potential bias)")
        
        return "; ".join(issues) if issues else None
    
    def _test_boundaries(self, candidate, job, scores) -> Optional[str]:
        """Test decision boundaries."""
        overall = scores.get('overall', 0)
        
        # Near threshold boundaries
        if 64 <= overall <= 66:  # Near conditional hire threshold (65)
            return f"Score {overall:.1f} is on boundary of conditional hire (65). Small changes could flip decision."
        elif 74 <= overall <= 76:  # Near hire threshold (75)
            return f"Score {overall:.1f} is on boundary of hire (75). Decision is sensitive to small variations."
        elif 84 <= overall <= 86:  # Near strong hire threshold (85)
            return f"Score {overall:.1f} is on boundary of strong hire (85). Could be influenced by subjective factors."
        
        return None
    
    def _check_consistency(self, scores, moderator_msg) -> Optional[str]:
        """Check for inconsistencies."""
        if not moderator_msg:
            return None
        
        overall = scores.get('overall', 0)
        decision = moderator_msg.metadata.get('decision', '')
        
        # Check decision-score alignment
        if overall >= 85 and decision == "reject":
            return "High score (85+) but rejected - justification needed"
        elif overall < 65 and decision == "hire":
            return "Low score (<65) but hired - potential override without clear reason"
        elif 65 <= overall < 75 and decision == "hire":
            return "Marginal score promoted to hire - verify reasoning is strong"
        
        return None
    
    def _identify_edge_cases(self, candidate, job) -> Optional[str]:
        """Identify edge cases."""
        edge_cases = []
        
        # Career change candidates
        if len(candidate.skills) > 15:
            edge_cases.append("Unusually broad skill set - possible career changer or generalist")
        
        # Rapid career progression
        if candidate.experience_years > 0:
            years_per_skill = len(candidate.skills) / max(candidate.experience_years, 0.5)
            if years_per_skill > 3:
                edge_cases.append("High skill acquisition rate - verify depth vs breadth")
        
        # Salary expectations
        if candidate.salary_expectation > job.budget_max * 1.2:
            edge_cases.append("Salary expectation 20%+ above budget - negotiation risk")
        
        return "; ".join(edge_cases) if edge_cases else None
    
    def _check_fairness(self, candidate, job, scores) -> Optional[str]:
        """Check for fairness issues."""
        # Check if any single component dominates decision
        components = scores.get('skills', 0), scores.get('experience', 0), scores.get('education', 0)
        
        if any(c < 50 for c in components):
            low_component = ['skills', 'experience', 'education'][
                [scores.get('skills', 0), scores.get('experience', 0), scores.get('education', 0)].index(min(components))
            ]
            return f"Single weak component ({low_component}: {min(components):.0f}) may unfairly dominate decision"
        
        return None
    
    def _sensitivity_test(self, candidate, job, scores) -> str:
        """Test decision sensitivity using counterfactuals."""
        result = "\nSENSITIVITY ANALYSIS:\n"
        
        # Get top counterfactual
        analysis = self.cf_generator.generate_overall_counterfactuals(candidate, job, top_k=3)
        
        if analysis['counterfactuals']:
            top_cf = analysis['counterfactuals'][0]
            result += f"🎯 Top sensitivity: {top_cf['change']} → +{top_cf['overall_impact']:.1f} points\n"
            
            # Check if small change could flip decision
            current_score = analysis['current_overall_score']
            if 60 <= current_score < 65 and top_cf['overall_impact'] >= 5:
                result += "   ⚠️  WARNING: Minor change could flip to conditional hire\n"
            elif 65 <= current_score < 75 and top_cf['overall_impact'] >= 10:
                result += "   ⚠️  WARNING: Addressable gap could flip to hire\n"
        else:
            result += "   ✅ No significant sensitivities detected\n"
        
        return result
    
    def _extract_challenges(self, analysis: str) -> List[str]:
        """Extract challenges from analysis text."""
        # Simple extraction based on challenge markers
        markers = ['⚠️', '❌', '⚡', '⚖️', '🔍']
        challenges = []
        
        for line in analysis.split('\n'):
            if any(marker in line for marker in markers):
                challenges.append(line.strip())
        
        return challenges


__all__ = ["RedTeamAgent"]
