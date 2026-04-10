"""Counterfactual Explanation Engine — generates what-if scenarios."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Dict, Any, Optional
from copy import deepcopy

from hiring_engine.schemas.candidate import CandidateProfile
from hiring_engine.schemas.job import JobRequirements
from hiring_engine.scoring.skills import calculate_skill_match
from hiring_engine.scoring.experience import calculate_experience_score
from hiring_engine.scoring.education import calculate_education_score
from hiring_engine.scoring.overall import calculate_overall_score

if TYPE_CHECKING:
    from hiring_engine.scoring.skill_matcher import SkillMatcher

logger = logging.getLogger(__name__)

# Skills with similarity >= this are "covered" and not truly missing
_COVERED_THRESHOLD = 0.60


class CounterfactualGenerator:
    """Generates counterfactual explanations for hiring decisions."""

    def __init__(self, skill_matcher: Optional["SkillMatcher"] = None):
        self._matcher = skill_matcher

    def generate_skill_counterfactuals(
        self, candidate: CandidateProfile, job: JobRequirements, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Shows: 'If candidate had skill X, score would increase by Y points'."""
        current_result = calculate_skill_match(
            candidate.skills, job.required_skills, job.preferred_skills,
            skill_matcher=self._matcher,
        )
        current_score = current_result["overall_score"]

        # With semantic matching, use similarity details to find gaps
        if self._matcher and "semantic_details" in current_result:
            return self._semantic_skill_counterfactuals(
                candidate, job, current_result, current_score, top_k
            )

        # Fallback: exact match logic
        missing_skills = [s for s in job.required_skills if s not in candidate.skills]
        return self._exact_skill_counterfactuals(
            candidate, job, missing_skills, current_score, top_k
        )

    def _semantic_skill_counterfactuals(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        current_result: Dict,
        current_score: float,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Counterfactuals based on semantic similarity gaps."""
        counterfactuals = []

        for detail in current_result["semantic_details"]:
            skill = detail["skill"]
            similarity = detail["similarity"]
            match_type = detail["match_type"]

            if match_type == "full":
                # Already fully matched — no counterfactual needed
                continue

            # Simulate adding the exact JD skill
            hypothetical_skills = candidate.skills + [skill]
            new_result = calculate_skill_match(
                hypothetical_skills, job.required_skills, job.preferred_skills,
                skill_matcher=self._matcher,
            )
            new_score = new_result["overall_score"]
            impact = new_score - current_score

            if match_type == "partial":
                explanation = (
                    f"Strengthen {skill} (currently {similarity:.0%} covered via "
                    f"{detail['best_match']}): skill score {current_score:.1f} → "
                    f"{new_score:.1f} (+{impact:.1f})"
                )
            else:
                explanation = (
                    f"Add {skill}: skill score {current_score:.1f} → "
                    f"{new_score:.1f} (+{impact:.1f})"
                )

            counterfactuals.append({
                "type": "skill",
                "change": f"Add skill: {skill}",
                "current_score": current_score,
                "new_score": new_score,
                "impact": impact,
                "similarity": similarity,
                "match_type": match_type,
                "explanation": explanation,
            })

        counterfactuals.sort(key=lambda x: x["impact"], reverse=True)
        return counterfactuals[:top_k]

    def _exact_skill_counterfactuals(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        missing_skills: List[str],
        current_score: float,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Original exact-match counterfactuals."""
        counterfactuals = []
        for skill in missing_skills[:top_k]:
            hypothetical_skills = candidate.skills + [skill]
            new_result = calculate_skill_match(
                hypothetical_skills, job.required_skills, job.preferred_skills,
            )
            new_score = new_result["overall_score"]
            impact = new_score - current_score

            counterfactuals.append({
                "type": "skill",
                "change": f"Add skill: {skill}",
                "current_score": current_score,
                "new_score": new_score,
                "impact": impact,
                "explanation": f"If candidate had {skill}, skill score would increase from {current_score:.1f} to {new_score:.1f} (+{impact:.1f})",
            })

        counterfactuals.sort(key=lambda x: x["impact"], reverse=True)
        return counterfactuals

    def generate_experience_counterfactuals(
        self, candidate: CandidateProfile, job: JobRequirements, scenarios: List[float] = None
    ) -> List[Dict[str, Any]]:
        """Shows: 'If candidate had N years, score would be X'."""
        current_result = calculate_experience_score(
            candidate.experience_years, job.min_experience_years, job.level
        )
        current_score = current_result["score"]

        if scenarios is None:
            scenarios = sorted(set([
                candidate.experience_years + 1,
                candidate.experience_years + 2,
                candidate.experience_years + 3,
                job.min_experience_years,
            ]))

        counterfactuals = []
        for years in scenarios:
            if years <= candidate.experience_years:
                continue
            new_result = calculate_experience_score(years, job.min_experience_years, job.level)
            new_score = new_result["score"]
            impact = new_score - current_score
            years_diff = years - candidate.experience_years

            counterfactuals.append({
                "type": "experience",
                "change": f"Add {years_diff:.0f} years experience (total: {years:.0f} years)",
                "years": years,
                "current_score": current_score,
                "new_score": new_score,
                "impact": impact,
                "meets_minimum": years >= job.min_experience_years,
                "explanation": f"If candidate had {years:.0f} years (+{years_diff:.0f}), experience score: {current_score:.1f} -> {new_score:.1f} (+{impact:.1f})",
            })
        return counterfactuals

    def generate_education_counterfactuals(
        self, candidate: CandidateProfile, job: JobRequirements
    ) -> List[Dict[str, Any]]:
        """Shows: 'If candidate had higher degree, score would be X'."""
        education_levels = ["High School", "Bachelor", "Master", "PhD"]
        current_result = calculate_education_score(candidate.education, job.required_education)
        current_score = current_result["score"]

        try:
            current_idx = education_levels.index(candidate.education)
        except ValueError:
            current_idx = 0

        counterfactuals = []
        for i in range(current_idx + 1, len(education_levels)):
            higher_ed = education_levels[i]
            new_result = calculate_education_score(higher_ed, job.required_education)
            new_score = new_result["score"]
            impact = new_score - current_score

            counterfactuals.append({
                "type": "education",
                "change": f"Upgrade to {higher_ed}",
                "current_score": current_score,
                "new_score": new_score,
                "impact": impact,
                "explanation": f"If candidate had {higher_ed} (vs {candidate.education}), education score: {current_score:.1f} -> {new_score:.1f} (+{impact:.1f})",
            })
        return counterfactuals

    def generate_salary_counterfactuals(
        self, candidate: CandidateProfile, job: JobRequirements, scenarios: List[int] = None
    ) -> List[Dict[str, Any]]:
        """Shows: 'If salary expectation was $X, budget fit would be Y'."""
        current_salary = candidate.salary_expectation

        if scenarios is None:
            scenarios = sorted(set([
                int(job.budget_max * 0.7),
                int(job.budget_max * 0.8),
                int(job.budget_max * 0.9),
                int(job.budget_max),
            ]))

        counterfactuals = []
        for salary in scenarios:
            if salary == current_salary:
                continue
            margin = job.budget_max - salary
            margin_pct = (margin / job.budget_max) * 100

            counterfactuals.append({
                "type": "salary",
                "change": f"Salary expectation: ${salary:,}",
                "current_salary": current_salary,
                "new_salary": salary,
                "difference": salary - current_salary,
                "within_budget": salary <= job.budget_max,
                "budget_margin": margin,
                "budget_margin_percentage": margin_pct,
                "explanation": f"If salary was ${salary:,} (vs ${current_salary:,}), budget margin: ${margin:,} ({margin_pct:.1f}%)",
            })
        return counterfactuals

    def generate_overall_counterfactuals(
        self, candidate: CandidateProfile, job: JobRequirements, top_k: int = 10
    ) -> Dict[str, Any]:
        """Generate comprehensive counterfactual analysis with overall score impact."""
        current_overall = calculate_overall_score(
            candidate, job, skill_matcher=self._matcher
        )
        current_score = current_overall["overall_score"]
        all_counterfactuals = []

        # Skills
        for cf in self.generate_skill_counterfactuals(candidate, job, top_k=5):
            skill = cf["change"].replace("Add skill: ", "")
            hypothetical = deepcopy(candidate)
            hypothetical.skills.append(skill)
            new_overall = calculate_overall_score(
                hypothetical, job, skill_matcher=self._matcher
            )
            all_counterfactuals.append({
                **cf,
                "overall_current": current_score,
                "overall_new": new_overall["overall_score"],
                "overall_impact": new_overall["overall_score"] - current_score,
            })

        # Experience
        for cf in self.generate_experience_counterfactuals(candidate, job):
            hypothetical = deepcopy(candidate)
            hypothetical.experience_years = cf.get("years", candidate.experience_years)
            new_overall = calculate_overall_score(
                hypothetical, job, skill_matcher=self._matcher
            )
            all_counterfactuals.append({
                **cf,
                "overall_current": current_score,
                "overall_new": new_overall["overall_score"],
                "overall_impact": new_overall["overall_score"] - current_score,
            })

        # Education
        for cf in self.generate_education_counterfactuals(candidate, job):
            overall_impact = cf["impact"] * 0.15  # Education is 15% of overall
            all_counterfactuals.append({
                **cf,
                "overall_current": current_score,
                "overall_new": current_score + overall_impact,
                "overall_impact": overall_impact,
            })

        all_counterfactuals.sort(key=lambda x: x["overall_impact"], reverse=True)

        return {
            "current_overall_score": current_score,
            "counterfactuals": all_counterfactuals[:top_k],
            "summary": {
                "total_scenarios": len(all_counterfactuals),
                "highest_impact": all_counterfactuals[0] if all_counterfactuals else None,
                "actionable_count": len([cf for cf in all_counterfactuals if cf["overall_impact"] > 5]),
            },
        }

    def get_actionable_feedback(
        self, candidate: CandidateProfile, job: JobRequirements, score_threshold: float = 75.0
    ) -> List[str]:
        """Generate actionable feedback for candidate improvement."""
        current_overall = calculate_overall_score(
            candidate, job, skill_matcher=self._matcher
        )
        current_score = current_overall["overall_score"]

        if current_score >= score_threshold:
            return [f"Already meets threshold ({current_score:.1f}/{score_threshold})"]

        gap = score_threshold - current_score
        recommendations = [f"Current score: {current_score:.1f}/100 (need {gap:.1f} more points to reach {score_threshold})"]

        analysis = self.generate_overall_counterfactuals(candidate, job, top_k=5)
        recommendations.append("\nTop ways to improve score:\n")
        for i, cf in enumerate(analysis["counterfactuals"][:5], 1):
            if cf["overall_impact"] > 0:
                recommendations.append(f"{i}. {cf['change']} -> +{cf['overall_impact']:.1f} points overall")

        return recommendations


__all__ = ["CounterfactualGenerator"]
