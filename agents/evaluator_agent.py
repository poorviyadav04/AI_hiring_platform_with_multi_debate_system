"""
Evaluator Agent - Objectively scores candidates using deterministic tools.
"""

from typing import Optional, Any, Dict
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent, AgentState
from tools.scoring import calculate_overall_score
from tools.constraints import validate_all_constraints
from data.schemas import HiringConstraints
import json


class EvaluatorAgent(BaseAgent):
    """
    Evaluator Agent: Provides objective, data-driven candidate assessment.
    
    Responsibilities:
    - Calculate all scoring metrics
    - Validate constraints
    - Provide factual assessment
    - No subjective opinions
    """
    
    SYSTEM_PROMPT = """You are an Evaluator Agent for hiring decisions.

Your role is to provide OBJECTIVE, DATA-DRIVEN assessments.

You MUST:
1. Use scoring tools to calculate exact metrics
2. Validate all constraints (budget, experience, scores)
3. Present facts and numbers
4. Avoid subjective opinions
5. Highlight both strengths and weaknesses equally

You must NOT:
- Make hiring recommendations (that's the Moderator's job)
- Show bias toward hiring or rejecting
- Use emotional language

Your output should be structured, factual, and comprehensive."""
    
    def __init__(self, llm: Optional[Any] = None, constraints: Optional[HiringConstraints] = None):
        """
        Initialize Evaluator Agent.
        
        Args:
            llm: LLM instance (not used in deterministic mode)
            constraints: Hiring constraints/policies
        """
        super().__init__(
            name="Evaluator",
            role="evaluator",
            system_prompt=self.SYSTEM_PROMPT,
            llm=llm
        )
        
        # Default constraints
        self.constraints = constraints or HiringConstraints(
            policy_id="POL-DEFAULT",
            policy_name="Standard Hiring Policy"
        )
    
    def run(self, state: AgentState) -> AgentState:
        """
        Evaluate candidate objectively using deterministic scoring.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with evaluation
        """
        candidate = state.candidate
        job = state.job
        
        # Calculate overall score
        score_result = calculate_overall_score(candidate, job)
        
        # Validate constraints
        validation_result = validate_all_constraints(
            candidate,
            job,
            score_result['overall_score'],
            self.constraints
        )
        
        # Store scores in state
        state.scores['overall'] = score_result['overall_score']
        state.scores['skills'] = score_result['component_scores']['skills']
        state.scores['experience'] = score_result['component_scores']['experience']
        state.scores['education'] = score_result['component_scores']['education']
        state.scores['interviews'] = score_result['component_scores']['interviews']
        
        # Build evaluation message
        evaluation = self._build_evaluation(score_result, validation_result)
        
        # Add message to state
        message = self.create_message(
            content=evaluation,
            metadata={
                'scores': score_result,
                'validation': validation_result
            }
        )
        state.messages.append(message)
        
        return state
    
    def _build_evaluation(self, score_result: Dict, validation_result: Dict) -> str:
        """Build formatted evaluation message."""
        
        eval_text = f"""OBJECTIVE EVALUATION REPORT
{'=' * 70}

OVERALL ASSESSMENT:
  Score: {score_result['overall_score']:.1f}/100
  Recommendation Tier: {score_result['recommendation'].upper()}

COMPONENT BREAKDOWN:
  Skills Match:     {score_result['component_scores']['skills']:.1f}/100 (40% weight)
  Experience Fit:   {score_result['component_scores']['experience']:.1f}/100 (30% weight)
  Education Level:  {score_result['component_scores']['education']:.1f}/100 (15% weight)
  Interview Scores: {score_result['component_scores']['interviews']:.1f}/100 (15% weight)

KEY FACTORS:
"""
        
        # Skills
        skill_details = score_result['detailed_breakdown']['skills']
        eval_text += f"\n  Skills:\n"
        if skill_details['missing_required']:
            eval_text += f"    ⚠️  Missing Required: {', '.join(skill_details['missing_required'])}\n"
        else:
            eval_text += f"    ✓ All required skills present\n"
        
        eval_text += f"    Matched: {len(skill_details['matched_required'])}/{len(skill_details['matched_required']) + len(skill_details['missing_required'])}\n"
        
        # Experience
        exp_details = score_result['detailed_breakdown']['experience']
        eval_text += f"\n  Experience:\n"
        if exp_details['gap_years'] > 0:
            eval_text += f"    Gap: {exp_details['gap_years']:.1f} years below requirement\n"
        elif exp_details['gap_years'] < 0:
            eval_text += f"    Exceeds requirement by {abs(exp_details['gap_years']):.1f} years\n"
        else:
            eval_text += f"    ✓ Meets requirement exactly\n"
        
        eval_text += f"    Meets Minimum: {exp_details['meets_minimum']}\n"
        
        # Education
        edu_details = score_result['detailed_breakdown']['education']
        eval_text += f"\n  Education:\n"
        eval_text += f"    Level Gap: {edu_details['difference']} levels\n"
        eval_text += f"    Meets Requirement: {edu_details['meets_requirement']}\n"
        
        # Constraint validation
        eval_text += f"\nCONSTRAINT VALIDATION:\n"
        eval_text += f"  Overall Compliance: {'✓ PASS' if validation_result['all_compliant'] else '✗ FAIL'}\n"
        eval_text += f"  Compliance Rate: {validation_result['compliance_rate']*100:.0f}%\n"
        
        if validation_result['violations']:
            eval_text += f"\n  ⚠️  VIOLATIONS ({len(validation_result['violations'])}):\n"
            for v in validation_result['violations']:
                eval_text += f"    • {v}\n"
        
        if validation_result['warnings']:
            eval_text += f"\n  ⚡ WARNINGS ({len(validation_result['warnings'])}):\n"
            for w in validation_result['warnings']:
                eval_text += f"    • {w}\n"
        
        eval_text += f"\n  Decision Recommendation: {validation_result['final_decision'].upper()}\n"
        eval_text += f"  Requires Escalation: {'Yes' if validation_result['requires_escalation'] else 'No'}\n"
        
        eval_text += f"\n{'=' * 70}\n"
        eval_text += "End of Objective Evaluation\n"
        
        return eval_text


__all__ = ["EvaluatorAgent"]
