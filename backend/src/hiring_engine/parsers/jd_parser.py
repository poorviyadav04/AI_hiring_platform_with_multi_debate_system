"""Job description parser using Gemini."""

import json
import logging
import random

from hiring_engine.llm.base import BaseLLMClient
from hiring_engine.schemas.job import JobRequirements, JDParseResult

logger = logging.getLogger(__name__)


async def parse_job_description(jd_text: str, llm: BaseLLMClient) -> JDParseResult:
    """Parse a job description into structured JobRequirements."""
    logger.info("Parsing job description (%d chars)", len(jd_text))

    prompt = f"""Extract structured job requirements from this job description.
Return ONLY a valid JSON object with these exact fields:
{{
    "job_id": "JOB-XXXX" (generate 4 random digits),
    "title": "Job Title",
    "department": "Department Name",
    "level": "junior" | "mid" | "senior" | "staff" | "principal",
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill3"],
    "min_experience_years": 3.0,
    "required_education": "BS Computer Science or equivalent",
    "budget_min": 80000,
    "budget_max": 120000,
    "team_size": 5,
    "work_mode": "remote" | "hybrid" | "onsite",
    "urgency": "low" | "medium" | "high" | "critical",
    "team_description": "description" or null,
    "key_responsibilities": ["resp1", "resp2"],
    "growth_opportunities": "description" or null
}}

If salary/budget is not mentioned, estimate reasonable market rates for the role.
If level is not explicit, infer from the title and requirements.

Job Description:
{jd_text}

Return ONLY the JSON object, no markdown, no explanation."""

    text = await llm.generate(prompt=prompt, temperature=0.2, max_tokens=2000)
    text = text.strip()

    # Strip markdown fences
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3].strip()
        if text.startswith("json"):
            text = text[4:].strip()

    data = json.loads(text)

    # Ensure required fields
    inferred = []
    if not data.get("job_id"):
        data["job_id"] = f"JOB-{random.randint(1000, 9999)}"
    if not data.get("required_skills"):
        data["required_skills"] = ["General"]
    if data.get("budget_min", 0) == 0 or data.get("budget_max", 0) == 0:
        data["budget_min"] = data.get("budget_min", 60000) or 60000
        data["budget_max"] = data.get("budget_max", 120000) or 120000
        inferred.append("budget_min and budget_max estimated from market rates")

    warnings = []
    if not data.get("required_education"):
        data["required_education"] = "Bachelor's degree or equivalent"
        inferred.append("required_education")
    if not data.get("department"):
        data["department"] = "Engineering"
    if not data.get("level"):
        data["level"] = "mid"
    if not data.get("work_mode"):
        data["work_mode"] = "hybrid"
    if data["budget_max"] < data["budget_min"]:
        data["budget_max"] = data["budget_min"] * 1.3
        warnings.append("budget_max was less than budget_min, adjusted")

    # Fix null lists — LLM sometimes returns null instead of []
    for list_field in ["preferred_skills", "key_responsibilities"]:
        if data.get(list_field) is None:
            data[list_field] = []

    job = JobRequirements.model_validate(data)

    return JDParseResult(
        job_requirements=job,
        confidence=0.85,
        warnings=warnings,
        inferred_fields=inferred,
    )


__all__ = ["parse_job_description"]
