"""
Generate synthetic candidate profiles and job requirements for testing.
Creates realistic, diverse data with edge cases and challenging scenarios.
"""

import json
import random
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

# Add parent directory to path to import schemas
import sys
sys.path.append(str(Path(__file__).parent.parent))

from data.schemas import CandidateProfile, JobRequirements, HiringConstraints


# Lists for generating realistic data
FIRST_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mason",
    "Isabella", "William", "Mia", "James", "Charlotte", "Benjamin", "Amelia",
    "Lucas", "Harper", "Henry", "Evelyn", "Alexander", "Abigail", "Michael",
    "Emily", "Daniel", "Elizabeth", "Matthew", "Sofia", "Jackson", "Avery",
    "Sebastian", "Ella", "David", "Scarlett", "Joseph", "Grace", "Carter",
    "Chloe", "Owen", "Victoria", "Wyatt", "Riley", "John", "Aria", "Jack",
    "Lily", "Luke", "Aubrey", "Jayden", "Zoey", "Dylan"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Patel", "Singh", "Kumar", "Chen", "Wang", "Li"
]

SKILLS_DATABASE = {
    "programming_languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go",
        "Rust", "Kotlin", "Swift", "Ruby", "PHP", "Scala", "R"
    ],
    "web_frameworks": [
        "React", "Vue.js", "Angular", "Next.js", "Django", "Flask",
        "FastAPI", "Express.js", "Spring Boot", "ASP.NET", "Ruby on Rails"
    ],
    "mobile": [
        "React Native", "Flutter", "Swift/iOS", "Kotlin/Android", "Xamarin"
    ],
    "databases": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "DynamoDB", "Cassandra", "Neo4j", "SQLite"
    ],
    "cloud": [
        "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes",
        "Terraform", "CloudFormation", "Serverless"
    ],
    "ml_ai": [
        "TensorFlow", "PyTorch", "Scikit-learn", "Hugging Face",
        "LangChain", "OpenAI API", "Computer Vision", "NLP"
    ],
    "devops": [
        "CI/CD", "Jenkins", "GitHub Actions", "GitLab CI", "Ansible",
        "Prometheus", "Grafana", "ELK Stack"
    ],
    "soft_skills": [
        "Leadership", "Communication", "Problem Solving", "Team Collaboration",
        "Mentoring", "Agile/Scrum", "Technical Writing", "Stakeholder Management"
    ]
}

COMPANIES = [
    "Google", "Amazon", "Microsoft", "Meta", "Apple", "Netflix", "Uber",
    "Airbnb", "Stripe", "Coinbase", "Shopify", "Square", "Slack",
    "Dropbox", "Twitter", "LinkedIn", "Adobe", "Salesforce", "Oracle",
    "IBM", "Intel", "NVIDIA", "TechStartup Inc", "DataCorp", "CloudSystems"
]

EDUCATION_LEVELS = [
    "High School Diploma",
    "Associate Degree in Computer Science",
    "BS Computer Science",
    "BS Software Engineering",
    "BS Information Technology",
    "BA Computer Science",
    "MS Computer Science",
    "MS Data Science",
    "MS Artificial Intelligence",
    "PhD Computer Science",
    "Bootcamp Graduate (Coding Bootcamp)"
]

CERTIFICATIONS = [
    "AWS Certified Solutions Architect",
    "AWS Certified Developer",
    "Google Cloud Professional",
    "Azure Fundamentals",
    "Certified Kubernetes Administrator (CKA)",
    "Certified Scrum Master (CSM)",
    "PMP (Project Management Professional)",
    "CISSP (Security)",
    "TensorFlow Developer Certificate"
]

JOB_TITLES = {
    "junior": [
        "Junior Software Engineer",
        "Associate Developer",
        "Software Engineer I",
        "Entry-Level Data Analyst"
    ],
    "mid": [
        "Software Engineer",
        "Full-Stack Developer",
        "Backend Engineer",
        "Frontend Engineer",
        "Data Engineer",
        "ML Engineer"
    ],
    "senior": [
        "Senior Software Engineer",
        "Senior Full-Stack Developer",
        "Senior Backend Engineer",
        "Senior Data Scientist",
        "Tech Lead"
    ],
    "staff": [
        "Staff Software Engineer",
        "Staff ML Engineer",
        "Principal Engineer"
    ]
}


def generate_candidate(candidate_id: int, difficulty: str = "normal") -> CandidateProfile:
    """
    Generate a realistic candidate profile.
    
    difficulty: 
        - "normal": standard qualified candidate
        - "edge_case": challenging scenario (overqualified, budget issues, skill gaps)
        - "perfect": ideal candidate
    """
    
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    name = f"{first_name} {last_name}"
    email = f"{first_name.lower()}.{last_name.lower()}@email.com"
    
    # Generate skills based on difficulty
    if difficulty == "perfect":
        num_skills = random.randint(8, 12)
        experience_years = random.uniform(5, 10)
        education = random.choice(EDUCATION_LEVELS[-5:])  # Advanced degrees
        tech_score = random.uniform(85, 100)
        behavioral_score = random.uniform(85, 95)
    elif difficulty == "edge_case":
        # Could be overqualified, underqualified, or missing key skills
        edge_type = random.choice(["overqualified", "underqualified", "skill_mismatch", "budget_issue"])
        
        if edge_type == "overqualified":
            num_skills = random.randint(10, 15)
            experience_years = random.uniform(12, 20)
            education = random.choice(EDUCATION_LEVELS[-3:])
            tech_score = random.uniform(90, 100)
            behavioral_score = random.uniform(80, 95)
        elif edge_type == "underqualified":
            num_skills = random.randint(3, 5)
            experience_years = random.uniform(0.5, 2)
            education = random.choice(EDUCATION_LEVELS[:4])
            tech_score = random.uniform(50, 70)
            behavioral_score = random.uniform(70, 85)
        elif edge_type == "skill_mismatch":
            num_skills = random.randint(6, 8)
            experience_years = random.uniform(3, 6)
            education = random.choice(EDUCATION_LEVELS[4:8])
            tech_score = random.uniform(65, 80)
            behavioral_score = random.uniform(75, 90)
        else:  # budget_issue
            num_skills = random.randint(7, 10)
            experience_years = random.uniform(6, 9)
            education = random.choice(EDUCATION_LEVELS[5:9])
            tech_score = random.uniform(80, 92)
            behavioral_score = random.uniform(80, 90)
    else:  # normal
        num_skills = random.randint(5, 9)
        experience_years = random.uniform(2, 8)
        education = random.choice(EDUCATION_LEVELS[3:9])
        tech_score = random.uniform(65, 88)
        behavioral_score = random.uniform(70, 88)
    
    # Select diverse skills
    skills = []
    skills.extend(random.sample(SKILLS_DATABASE["programming_languages"], min(2, num_skills)))
    skills.extend(random.sample(SKILLS_DATABASE["web_frameworks"], min(2, num_skills - len(skills))))
    skills.extend(random.sample(SKILLS_DATABASE["databases"], min(1, num_skills - len(skills))))
    skills.extend(random.sample(SKILLS_DATABASE["cloud"], min(1, num_skills - len(skills))))
    
    # Add ML/AI skills occasionally
    if random.random() > 0.7:
        skills.extend(random.sample(SKILLS_DATABASE["ml_ai"], min(2, num_skills - len(skills))))
    
    # Add soft skills
    skills.extend(random.sample(SKILLS_DATABASE["soft_skills"], min(2, num_skills - len(skills))))
    
    # Certifications (more likely for experienced candidates)
    certifications = []
    if experience_years > 3 and random.random() > 0.6:
        certifications = random.sample(CERTIFICATIONS, random.randint(1, 3))
    
    # Salary expectation scaled with experience and difficulty
    base_salary = 60000 + (experience_years * 12000)
    if difficulty == "perfect":
        salary_expectation = base_salary * random.uniform(1.1, 1.3)
    elif difficulty == "edge_case" and edge_type == "budget_issue":
        salary_expectation = base_salary * random.uniform(1.3, 1.6)  # High expectations
    else:
        salary_expectation = base_salary * random.uniform(0.9, 1.15)
    
    # Work preference
    work_preference = random.choice(["remote", "hybrid", "onsite"])
    
    # Current position
    years_int = int(experience_years)
    if years_int < 2:
        level = "junior"
    elif years_int < 5:
        level = "mid"
    elif years_int < 10:
        level = "senior"
    else:
        level = "staff"
    
    current_title = random.choice(JOB_TITLES.get(level, JOB_TITLES["mid"]))
    current_company = random.choice(COMPANIES)
    
    # Notable projects
    notable_projects = []
    if random.random() > 0.5:
        project_types = [
            "Built microservices architecture serving 10M+ users",
            "Led migration from monolith to serverless",
            "Developed real-time analytics dashboard",
            "Implemented ML-based recommendation system",
            "Built internal developer tools used by 200+ engineers",
            "Reduced cloud costs by 40% through optimization"
        ]
        notable_projects = random.sample(project_types, random.randint(1, 3))
    
    return CandidateProfile(
        candidate_id=f"CAND-{candidate_id:04d}",
        name=name,
        email=email,
        phone=f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
        skills=skills[:num_skills],
        experience_years=round(experience_years, 1),
        education=education,
        certifications=certifications,
        technical_interview_score=round(tech_score, 1),
        behavioral_interview_score=round(behavioral_score, 1),
        coding_challenge_score=round(min(100, max(0, random.uniform(tech_score - 10, min(100, tech_score + 5)))), 1),
        salary_expectation=round(salary_expectation, -3),  # Round to nearest 1000
        work_preference=work_preference,
        availability_date=(datetime.now() + timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d"),
        willing_to_relocate=random.choice([True, False]),
        current_title=current_title,
        current_company=current_company,
        notable_projects=notable_projects,
        github_url=f"https://github.com/{first_name.lower()}{last_name.lower()}",
        linkedin_url=f"https://linkedin.com/in/{first_name.lower()}-{last_name.lower()}"
    )


def generate_job_requirements(job_id: int) -> JobRequirements:
    """Generate realistic job requirements."""
    
    level = random.choice(["junior", "mid", "senior", "staff"])
    title = random.choice(JOB_TITLES[level])
    department = random.choice([
        "Engineering", "Data Science", "Platform", "Infrastructure",
        "Product Engineering", "AI/ML", "Security"
    ])
    
    # Skills based on job level
    if level == "junior":
        num_required = random.randint(3, 5)
        num_preferred = random.randint(2, 4)
        min_exp = random.uniform(0, 2)
        budget_min, budget_max = 60000, 85000
    elif level == "mid":
        num_required = random.randint(4, 6)
        num_preferred = random.randint(3, 5)
        min_exp = random.uniform(2, 5)
        budget_min, budget_max = 85000, 130000
    elif level == "senior":
        num_required = random.randint(5, 8)
        num_preferred = random.randint(4, 6)
        min_exp = random.uniform(5, 8)
        budget_min, budget_max = 130000, 180000
    else:  # staff
        num_required = random.randint(6, 10)
        num_preferred = random.randint(5, 8)
        min_exp = random.uniform(8, 12)
        budget_min, budget_max = 180000, 250000
    
    # Select required skills
    required_skills = []
    required_skills.extend(random.sample(SKILLS_DATABASE["programming_languages"], min(2, num_required)))
    required_skills.extend(random.sample(SKILLS_DATABASE["web_frameworks"], min(1, num_required - len(required_skills))))
    required_skills.extend(random.sample(SKILLS_DATABASE["databases"], min(1, num_required - len(required_skills))))
    
    # Preferred skills
    all_skills = [s for cat in SKILLS_DATABASE.values() for s in cat]
    available_preferred = [s for s in all_skills if s not in required_skills]
    preferred_skills = random.sample(available_preferred, min(num_preferred, len(available_preferred)))
    
    # Education requirement
    if level in ["junior", "mid"]:
        required_education = "BS Computer Science or equivalent"
    else:
        required_education = random.choice([
            "BS Computer Science or equivalent",
            "MS Computer Science preferred",
            "Advanced degree in Computer Science or related field"
        ])
    
    # Work mode
    work_mode = random.choice(["remote", "hybrid", "onsite"])
    
    # Urgency
    urgency = random.choice(["low", "medium", "high", "critical"])
    
    # Responsibilities
    responsibilities = [
        f"Design and implement scalable {random.choice(['backend', 'frontend', 'full-stack'])} solutions",
        "Collaborate with cross-functional teams to define and ship features",
        "Write clean, maintainable code with comprehensive tests",
        "Participate in code reviews and mentor junior engineers" if level in ["senior", "staff"] else "Learn from senior engineers",
        "Contribute to architectural decisions" if level in ["senior", "staff"] else "Implement features based on architectural guidelines"
    ]
    
    return JobRequirements(
        job_id=f"JOB-{job_id:04d}",
        title=title,
        department=department,
        level=level,
        required_skills=required_skills[:num_required],
        preferred_skills=preferred_skills,
        min_experience_years=round(min_exp, 1),
        required_education=required_education,
        budget_min=budget_min,
        budget_max=budget_max,
        team_size=random.randint(3, 15),
        work_mode=work_mode,
        urgency=urgency,
        team_description=f"Fast-paced {department} team building cutting-edge products",
        key_responsibilities=responsibilities,
        growth_opportunities="Strong mentorship, learning budget, conference attendance" if random.random() > 0.5 else None
    )


def generate_hiring_constraints() -> HiringConstraints:
    """Generate default hiring policies."""
    
    return HiringConstraints(
        policy_id="POLICY-001",
        policy_name="Standard Hiring Policy 2024",
        max_budget_overage_percent=5.0,
        require_vp_approval_above=150000,
        allow_experience_gap=True,
        max_experience_gap_years=1.0,
        require_work_authorization=True,
        require_background_check=True,
        equal_opportunity_employer=True,
        prioritize_internal_candidates=True,
        diversity_hiring_goals=True,
        min_technical_score=60.0,
        min_behavioral_score=60.0,
        min_overall_score=65.0
    )


def main():
    """Generate and save synthetic data."""
    
    print("🧠 LLM Decision Intelligence System - Data Generator")
    print("=" * 60)
    
    # Create data directory
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Generate candidates
    print("\n📊 Generating candidate profiles...")
    candidates = []
    
    # 70% normal candidates
    for i in range(140):
        candidates.append(generate_candidate(i + 1, "normal"))
    
    # 20% edge cases
    for i in range(40):
        candidates.append(generate_candidate(i + 141, "edge_case"))
    
    # 10% perfect candidates
    for i in range(20):
        candidates.append(generate_candidate(i + 181, "perfect"))
    
    print(f"   ✓ Generated {len(candidates)} candidate profiles")
    
    # Save candidates as CSV
    csv_path = data_dir / "candidates.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        if candidates:
            fieldnames = candidates[0].dict().keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for candidate in candidates:
                writer.writerow(candidate.dict())
    
    print(f"   ✓ Saved to {csv_path}")
    
    # Save candidates as JSON (for easier programmatic access)
    json_path = data_dir / "candidates.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump([c.dict() for c in candidates], f, indent=2, default=str)
    
    print(f"   ✓ Saved to {json_path}")
    
    # Generate job requirements
    print("\n💼 Generating job requirements...")
    jobs = []
    for i in range(15):
        jobs.append(generate_job_requirements(i + 1))
    
    print(f"   ✓ Generated {len(jobs)} job postings")
    
    jobs_path = data_dir / "job_requirements.json"
    with open(jobs_path, 'w', encoding='utf-8') as f:
        json.dump([j.dict() for j in jobs], f, indent=2, default=str)
    
    print(f"   ✓ Saved to {jobs_path}")
    
    # Generate hiring constraints
    print("\n📋 Generating hiring policies...")
    constraints = generate_hiring_constraints()
    
    constraints_path = data_dir / "policies.json"
    with open(constraints_path, 'w', encoding='utf-8') as f:
        json.dump(constraints.dict(), f, indent=2)
    
    print(f"   ✓ Saved to {constraints_path}")
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("📈 Dataset Summary:")
    print("=" * 60)
    
    print(f"\nCandidates: {len(candidates)}")
    print(f"  - Normal: {sum(1 for c in candidates if 2 <= c.experience_years <= 8)}")
    print(f"  - Edge cases: {sum(1 for c in candidates if c.experience_years > 10 or c.experience_years < 2)}")
    print(f"  - Perfect fits: {sum(1 for c in candidates if c.technical_interview_score > 85)}")
    
    print(f"\nJobs: {len(jobs)}")
    for level in ["junior", "mid", "senior", "staff"]:
        count = sum(1 for j in jobs if j.level == level)
        print(f"  - {level.capitalize()}: {count}")
    
    avg_salary = sum(c.salary_expectation for c in candidates) / len(candidates)
    print(f"\nAverage Salary Expectation: ${avg_salary:,.0f}")
    
    print("\n✅ Data generation complete!")
    print(f"\n📁 Files created in {data_dir}/:")
    print("   - candidates.csv")
    print("   - candidates.json")
    print("   - job_requirements.json")
    print("   - policies.json")


if __name__ == "__main__":
    main()
