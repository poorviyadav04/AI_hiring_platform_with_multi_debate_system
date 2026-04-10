"""Parsers package."""
from hiring_engine.parsers.resume_parser import parse_resume
from hiring_engine.parsers.jd_parser import parse_job_description

__all__ = ["parse_resume", "parse_job_description"]
