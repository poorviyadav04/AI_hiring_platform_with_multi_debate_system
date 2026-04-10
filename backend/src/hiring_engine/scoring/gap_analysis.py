"""Gap analysis — identifies what a candidate is missing and generates improvement roadmap."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional

from hiring_engine.schemas.candidate import CandidateProfile
from hiring_engine.schemas.job import JobRequirements
from hiring_engine.schemas.api_models import GapItem, RoadmapItem
from hiring_engine.scoring.overall import calculate_overall_score
from hiring_engine.counterfactuals.generator import CounterfactualGenerator
from hiring_engine.llm.base import BaseLLMClient

if TYPE_CHECKING:
    from hiring_engine.scoring.skill_matcher import SkillMatcher

logger = logging.getLogger(__name__)


class GapAnalyzer:
    """Identifies gaps between a candidate and job requirements."""

    def __init__(self, skill_matcher: Optional["SkillMatcher"] = None):
        self._matcher = skill_matcher
        self._cf = CounterfactualGenerator(skill_matcher=skill_matcher)

    def analyze_gaps(
        self, candidate: CandidateProfile, job: JobRequirements
    ) -> List[GapItem]:
        """Identify all gaps with severity and impact."""
        score_result = calculate_overall_score(
            candidate, job, skill_matcher=self._matcher
        )
        gaps: List[GapItem] = []

        # Skill gaps — use semantic details when available
        skill_breakdown = score_result["detailed_breakdown"]["skills"]
        semantic_details = skill_breakdown.get("semantic_details")

        if semantic_details:
            self._semantic_skill_gaps(semantic_details, gaps)
        else:
            self._exact_skill_gaps(score_result, candidate, job, gaps)

        # Experience gap
        exp_gap = score_result["key_factors"]["experience_gap"]
        if exp_gap > 0:
            severity = "critical" if exp_gap > 2 else "moderate" if exp_gap > 1 else "minor"
            gaps.append(GapItem(
                category="experience",
                item=f"{exp_gap:.1f} years below requirement",
                severity=severity,
                impact_points=round(exp_gap * 6, 1),
                suggestion=f"Gain {exp_gap:.0f}+ years of relevant experience through work or significant side projects",
            ))

        # Education gap
        edu_gap = score_result["key_factors"]["education_gap"]
        if edu_gap < 0:
            severity = "moderate" if abs(edu_gap) == 1 else "critical"
            gaps.append(GapItem(
                category="education",
                item=f"{abs(edu_gap)} level(s) below requirement",
                severity=severity,
                impact_points=round(abs(edu_gap) * 3, 1),
                suggestion="Consider pursuing a higher degree or equivalent certification",
            ))

        gaps.sort(key=lambda g: g.impact_points, reverse=True)
        return gaps

    def _semantic_skill_gaps(
        self, semantic_details: List[dict], gaps: List[GapItem]
    ) -> None:
        """Build gaps from semantic matching details.

        Severity is based on similarity:
          < 0.40 → critical (skill barely related to anything the candidate has)
          0.40-0.59 → moderate (some overlap but not enough)
          0.60-0.79 → minor (partially covered, just needs strengthening)
          >= 0.80 → no gap
        """
        for detail in semantic_details:
            similarity = detail["similarity"]
            match_type = detail["match_type"]
            skill = detail["skill"]

            if match_type == "full":
                continue  # no gap

            coverage_deficit = 1.0 - similarity
            impact = round(coverage_deficit * 28, 1)  # 28 = 70 (required weight) * 0.4 (skill weight)

            if similarity < 0.40:
                severity = "critical"
                suggestion = f"Learn {skill} through online courses, projects, or certifications"
            elif similarity < 0.60:
                severity = "moderate"
                suggestion = f"Build deeper expertise in {skill} — you have some related skills"
            else:
                severity = "minor"
                best_match = detail.get("best_match", "")
                suggestion = (
                    f"Strengthen {skill} — partially covered via {best_match} "
                    f"({similarity:.0%} match)"
                )

            gaps.append(GapItem(
                category="skill",
                item=skill,
                severity=severity,
                impact_points=impact,
                suggestion=suggestion,
            ))

    def _exact_skill_gaps(
        self,
        score_result: dict,
        candidate: CandidateProfile,
        job: JobRequirements,
        gaps: List[GapItem],
    ) -> None:
        """Fallback: build gaps from exact match missing skills."""
        missing_required = score_result["key_factors"]["missing_required_skills"]
        cf_skills = self._cf.generate_skill_counterfactuals(candidate, job, top_k=10)
        cf_map = {cf["change"].replace("Add skill: ", ""): cf for cf in cf_skills}

        for skill in missing_required:
            cf = cf_map.get(skill, {})
            impact = cf.get("impact", 0)
            severity = "critical" if impact > 10 else "moderate" if impact > 5 else "minor"
            gaps.append(GapItem(
                category="skill",
                item=skill,
                severity=severity,
                impact_points=round(impact * 0.4, 1),
                suggestion=f"Learn {skill} through online courses, projects, or certifications",
            ))

    async def generate_roadmap(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        gaps: List[GapItem],
        llm: Optional[BaseLLMClient] = None,
    ) -> List[RoadmapItem]:
        """Generate a personalized learning roadmap."""
        if not gaps:
            return []

        if llm:
            return await self._generate_roadmap_llm(candidate, job, gaps, llm)

        # Deterministic fallback
        roadmap: List[RoadmapItem] = []
        for gap in gaps:
            if gap.category == "skill":
                roadmap.append(RoadmapItem(
                    skill=gap.item,
                    priority="high" if gap.severity == "critical" else "medium" if gap.severity == "moderate" else "low",
                    estimated_weeks=4 if gap.severity == "critical" else 2,
                    resources=[
                        f"Online course: {gap.item} fundamentals",
                        f"Build a project using {gap.item}",
                        f"Get {gap.item} certification if available",
                    ],
                    impact_on_score=gap.impact_points,
                ))
        return roadmap[:10]

    async def _generate_roadmap_llm(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        gaps: List[GapItem],
        llm: BaseLLMClient,
    ) -> List[RoadmapItem]:
        """Use LLM to generate a detailed learning roadmap."""
        gap_descriptions = "\n".join(
            f"- {g.category}: {g.item} (severity: {g.severity}, impact: +{g.impact_points} points)"
            for g in gaps[:8]
        )

        prompt = f"""Generate a learning roadmap for a candidate applying to {job.title} ({job.level} level).

Current skills: {', '.join(candidate.skills[:10])}
Experience: {candidate.experience_years} years

Gaps to close:
{gap_descriptions}

For each gap, provide:
1. The skill/area name
2. Priority (high/medium/low)
3. Estimated weeks to gain basic proficiency (must be between 1 and 52)
4. 2-3 specific resources (real course names, platforms, or project ideas)

Return a JSON array of objects with fields: skill, priority, estimated_weeks, resources (array of strings).
Return ONLY the JSON array, no markdown."""

        try:
            text = await llm.generate(prompt=prompt, temperature=0.4, max_tokens=1500)
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3].strip()
                if text.startswith("json"):
                    text = text[4:].strip()

            import json
            items = json.loads(text)
            roadmap = []
            for item in items[:10]:
                gap_match = next((g for g in gaps if g.item.lower() in item.get("skill", "").lower()), None)
                roadmap.append(RoadmapItem(
                    skill=item.get("skill", "Unknown"),
                    priority=item.get("priority", "medium"),
                    estimated_weeks=item.get("estimated_weeks", 4),
                    resources=item.get("resources", []),
                    impact_on_score=gap_match.impact_points if gap_match else 0,
                ))
            return roadmap
        except Exception as e:
            logger.warning("LLM roadmap generation failed: %s, using fallback", e)
            return await self.generate_roadmap(candidate, job, gaps, llm=None)


__all__ = ["GapAnalyzer"]
