"""Evaluator Agent - Objectively scores candidates using deterministic tools."""

import logging
from typing import Optional, Any, Dict

from hiring_engine.agents.base_agent import BaseAgent, AgentState
from hiring_engine.scoring.overall import calculate_overall_score
from hiring_engine.constraints.validator import validate_all_constraints
from hiring_engine.schemas.constraints import HiringConstraints

logger = logging.getLogger(__name__)


class EvaluatorAgent(BaseAgent):
    """Evaluator Agent: Provides objective, data-driven candidate assessment."""

    SYSTEM_PROMPT = """You are an Evaluator Agent for hiring decisions.
Your role is to provide OBJECTIVE, DATA-DRIVEN assessments.
You MUST use scoring tools, validate constraints, present facts and numbers.
You must NOT make hiring recommendations or show bias."""

    def __init__(self, llm: Optional[Any] = None, constraints: Optional[HiringConstraints] = None):
        super().__init__(name="Evaluator", role="evaluator", system_prompt=self.SYSTEM_PROMPT, llm=llm)
        self.constraints = constraints or HiringConstraints(policy_id="POL-DEFAULT", policy_name="Standard Hiring Policy")

    async def run(self, state: AgentState) -> AgentState:
        """Evaluate candidate objectively using deterministic scoring."""
        candidate = state.candidate
        job = state.job

        score_result = calculate_overall_score(candidate, job)
        validation_result = validate_all_constraints(candidate, job, score_result["overall_score"], self.constraints)

        state.scores["overall"] = score_result["overall_score"]
        state.scores["skills"] = score_result["component_scores"]["skills"]
        state.scores["experience"] = score_result["component_scores"]["experience"]
        state.scores["education"] = score_result["component_scores"]["education"]

        evaluation = self._build_evaluation(score_result, validation_result)
        message = self.create_message(content=evaluation, metadata={"scores": score_result, "validation": validation_result})
        state.messages.append(message)

        logger.info("Evaluator complete: score=%.1f recommendation=%s", score_result["overall_score"], score_result["recommendation"])
        return state

    def _build_evaluation(self, score_result: Dict, validation_result: Dict) -> str:
        eval_text = f"""OBJECTIVE EVALUATION REPORT
{'=' * 70}

OVERALL ASSESSMENT:
  Score: {score_result['overall_score']:.1f}/100
  Recommendation Tier: {score_result['recommendation'].upper()}

COMPONENT BREAKDOWN:
  Skills Match:     {score_result['component_scores']['skills']:.1f}/100 (50% weight)
  Experience Fit:   {score_result['component_scores']['experience']:.1f}/100 (35% weight)
  Education Level:  {score_result['component_scores']['education']:.1f}/100 (15% weight)

KEY FACTORS:
"""
        skill_details = score_result["detailed_breakdown"]["skills"]
        if skill_details["missing_required"]:
            eval_text += f"\n  Skills:\n    Missing Required: {', '.join(skill_details['missing_required'])}\n"
        else:
            eval_text += f"\n  Skills:\n    All required skills present\n"
        eval_text += f"    Matched: {len(skill_details['matched_required'])}/{len(skill_details['matched_required']) + len(skill_details['missing_required'])}\n"

        exp_details = score_result["detailed_breakdown"]["experience"]
        eval_text += f"\n  Experience:\n"
        if exp_details["gap_years"] > 0:
            eval_text += f"    Gap: {exp_details['gap_years']:.1f} years below requirement\n"
        elif exp_details["gap_years"] < 0:
            eval_text += f"    Exceeds requirement by {abs(exp_details['gap_years']):.1f} years\n"
        else:
            eval_text += f"    Meets requirement exactly\n"
        eval_text += f"    Meets Minimum: {exp_details['meets_minimum']}\n"

        edu_details = score_result["detailed_breakdown"]["education"]
        eval_text += f"\n  Education:\n    Level Gap: {edu_details['difference']} levels\n    Meets Requirement: {edu_details['meets_requirement']}\n"

        eval_text += f"\nCONSTRAINT VALIDATION:\n"
        eval_text += f"  Overall Compliance: {'PASS' if validation_result['all_compliant'] else 'FAIL'}\n"
        eval_text += f"  Compliance Rate: {validation_result['compliance_rate']*100:.0f}%\n"
        if validation_result["violations"]:
            eval_text += f"\n  VIOLATIONS ({len(validation_result['violations'])}):\n"
            for v in validation_result["violations"]:
                eval_text += f"    - {v}\n"
        if validation_result["warnings"]:
            eval_text += f"\n  WARNINGS ({len(validation_result['warnings'])}):\n"
            for w in validation_result["warnings"]:
                eval_text += f"    - {w}\n"
        eval_text += f"\n  Decision Recommendation: {validation_result['final_decision'].upper()}\n"
        eval_text += f"  Requires Escalation: {'Yes' if validation_result['requires_escalation'] else 'No'}\n"
        eval_text += f"\n{'=' * 70}\n"
        return eval_text


__all__ = ["EvaluatorAgent"]
