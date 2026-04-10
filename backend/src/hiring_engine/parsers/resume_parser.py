"""Resume PDF parser — extracts text then uses LLM to structure it."""

import json
import logging
import random

from hiring_engine.llm.base import BaseLLMClient
from hiring_engine.schemas.candidate import CandidateProfile, ResumeParseResult

logger = logging.getLogger(__name__)


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using built-in methods."""
    # Try pypdf first
    try:
        import io
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        if text.strip():
            return text.strip()
    except ImportError:
        pass
    except Exception as e:
        logger.warning("pypdf extraction failed: %s", e)

    # Fallback: basic decode attempt
    try:
        text = pdf_bytes.decode("utf-8", errors="ignore")
        # Filter to printable lines
        lines = [l for l in text.split("\n") if l.strip() and len(l.strip()) > 3]
        return "\n".join(lines[:200])
    except Exception:
        pass

    return ""


async def parse_resume(pdf_bytes: bytes, llm: BaseLLMClient) -> ResumeParseResult:
    """Parse a resume PDF into a structured CandidateProfile."""
    logger.info("Parsing resume (%d bytes)", len(pdf_bytes))

    # Step 1: Extract text from PDF
    raw_text = _extract_pdf_text(pdf_bytes)
    if not raw_text or len(raw_text) < 20:
        raise ValueError("Could not extract text from PDF. Please ensure it's a valid, text-based PDF.")

    logger.info("Extracted %d chars from PDF", len(raw_text))

    # Step 2: Use LLM to structure the text
    prompt = f"""Extract all information from this resume text and return a JSON object with these exact fields:
{{
    "candidate_id": "CAND-XXXX" (generate 4 random digits),
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "+1-555-000-0000" or null,
    "skills": ["skill1", "skill2"],
    "experience_years": 5.0,
    "education": "BS Computer Science",
    "certifications": [],
    "salary_expectation": 0,
    "work_preference": "hybrid",
    "current_title": "Software Engineer" or null,
    "current_company": "Company" or null,
    "notable_projects": ["project1"],
    "github_url": "https://github.com/user" or null,
    "linkedin_url": "https://linkedin.com/in/user" or null
}}

RESUME TEXT:
{raw_text[:4000]}

Return ONLY valid JSON, no markdown fences, no explanation."""

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
    if not data.get("candidate_id"):
        data["candidate_id"] = f"CAND-{random.randint(1000, 9999)}"
    if not data.get("skills"):
        data["skills"] = ["General"]
    if not data.get("email"):
        data["email"] = "unknown@example.com"
    if not data.get("name"):
        data["name"] = "Unknown Candidate"
    if not data.get("education"):
        data["education"] = "Not specified"
    # Fix null lists
    for list_field in ["skills", "certifications", "notable_projects"]:
        if data.get(list_field) is None:
            data[list_field] = []
    # Fix null enums
    if data.get("work_preference") not in ("remote", "hybrid", "onsite"):
        data["work_preference"] = "hybrid"
    # Fix null numbers
    if data.get("experience_years") is None:
        data["experience_years"] = 0
    if data.get("salary_expectation") is None:
        data["salary_expectation"] = 0

    # Validate experience years — clamp to sane range
    raw_exp = data["experience_years"]
    if raw_exp < 0:
        data["experience_years"] = 0
    elif raw_exp > 50:
        data["experience_years"] = 50

    warnings = []
    if raw_exp != data["experience_years"]:
        warnings.append(
            f"Experience years adjusted from {raw_exp} to {data['experience_years']} (out of valid range)"
        )
    if data.get("salary_expectation", 0) == 0:
        warnings.append("Salary expectation not found in resume, set to 0")
    if not data.get("github_url"):
        warnings.append("No GitHub URL found in resume")

    candidate = CandidateProfile.model_validate(data)

    return ResumeParseResult(
        candidate_profile=candidate,
        raw_text=raw_text[:500],
        confidence=0.85,
        warnings=warnings,
        github_url=data.get("github_url"),
        linkedin_url=data.get("linkedin_url"),
    )


__all__ = ["parse_resume"]
