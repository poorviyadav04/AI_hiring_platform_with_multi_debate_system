"""Centralized prompt templates for LLM operations."""

RESUME_PARSE_PROMPT = """Extract structured information from this resume. Return a JSON object with these fields:

- candidate_id: Generate as "CAND-" followed by 4 random digits
- name: Full name
- email: Email address
- phone: Phone number (or null)
- skills: Array of technical and soft skills mentioned
- experience_years: Total years of professional experience (estimate from work history)
- education: Highest degree (e.g., "BS Computer Science", "MS Data Science")
- certifications: Array of certifications mentioned
- technical_interview_score: null (not available from resume)
- behavioral_interview_score: null (not available from resume)
- coding_challenge_score: null (not available from resume)
- salary_expectation: 0 (not typically in resume, set to 0)
- work_preference: "hybrid" (default, unless stated)
- current_title: Current or most recent job title
- current_company: Current or most recent company
- notable_projects: Array of notable projects or achievements
- github_url: GitHub URL if found (or null)
- linkedin_url: LinkedIn URL if found (or null)

Resume content:
{resume_text}"""

JD_PARSE_PROMPT = """Extract structured job requirements from this job description. Return a JSON object with these fields:

- job_id: Generate as "JOB-" followed by 4 random digits
- title: Job title
- department: Department name (infer if not stated)
- level: One of "junior", "mid", "senior", "staff", "principal" (infer from title/requirements)
- required_skills: Array of must-have skills
- preferred_skills: Array of nice-to-have skills
- min_experience_years: Minimum years of experience required (number)
- required_education: Education requirement (e.g., "BS Computer Science or equivalent")
- budget_min: Minimum salary (estimate from market if not stated, use 0 if unknown)
- budget_max: Maximum salary (estimate from market if not stated, use 0 if unknown)
- team_size: Team size if mentioned (default 5)
- work_mode: One of "remote", "hybrid", "onsite" (infer if not stated)
- urgency: One of "low", "medium", "high", "critical" (default "medium")
- team_description: Brief team description if available
- key_responsibilities: Array of key responsibilities
- growth_opportunities: Growth opportunities if mentioned (or null)

Job Description:
{jd_text}"""

GAP_ANALYSIS_PROMPT = """Based on this candidate's evaluation against a job, generate a personalized learning roadmap.

Candidate Score: {overall_score}/100
Missing Skills: {missing_skills}
Experience Gap: {experience_gap} years
Education Gap: {education_gap}

For each gap, provide:
1. Priority (high/medium/low based on score impact)
2. Estimated time to close (in weeks)
3. 2-3 specific resources (courses, certifications, projects)
4. Expected score improvement

Focus on actionable, realistic improvements. Be specific about resources."""

GITHUB_CODE_REVIEW_PROMPT = """Analyze this code sample from a GitHub repository.

Repository: {repo_name}
Language: {language}
Claimed Skills: {claimed_skills}

Code:
```
{code_sample}
```

Evaluate:
1. Code quality (0-100): structure, naming, error handling, patterns
2. Skill level: beginner, intermediate, advanced
3. Does this code demonstrate proficiency in the claimed skills?
4. Is this original work or likely copied from a tutorial/template?
5. Testing presence and quality
6. Documentation quality

Be concise and specific."""
