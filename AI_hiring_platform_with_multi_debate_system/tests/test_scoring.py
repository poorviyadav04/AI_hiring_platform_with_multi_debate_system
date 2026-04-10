"""
Unit tests for deterministic scoring functions.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.scoring import (
    calculate_skill_match,
    calculate_experience_score,
    calculate_education_score,
    calculate_overall_score,
)
from data.schemas import CandidateProfile, JobRequirements


class TestSkillMatch:
    """Test skill matching algorithm."""
    
    def test_perfect_required_match(self):
        """Test 100% match on required skills."""
        result = calculate_skill_match(
            candidate_skills=["Python", "React", "AWS"],
            required_skills=["Python", "React", "AWS"],
            preferred_skills=[]
        )
        
        assert result["required_match_score"] == 100
        assert len(result["matched_required"]) == 3
        assert len(result["missing_required"]) == 0
    
    def test_partial_required_match(self):
        """Test partial match on required skills."""
        result = calculate_skill_match(
            candidate_skills=["Python", "React"],
            required_skills=["Python", "React", "AWS", "Docker"],
            preferred_skills=[]
        )
        
        assert result["required_match_score"] == 50.0  # 2 out of 4
        assert len(result["matched_required"]) == 2
        assert len(result["missing_required"]) == 2
        assert "AWS" in result["missing_required"]
        assert "Docker" in result["missing_required"]
    
    def test_case_insensitive_matching(self):
        """Test that skill matching is case-insensitive."""
        result = calculate_skill_match(
            candidate_skills=["python", "REACT", "Aws"],
            required_skills=["Python", "React", "AWS"],
            preferred_skills=[]
        )
        
        assert result["required_match_score"] == 100
        assert len(result["matched_required"]) == 3
    
    def test_preferred_skills_bonus(self):
        """Test that preferred skills increase score."""
        result = calculate_skill_match(
            candidate_skills=["Python", "React", "AWS", "Docker"],
            required_skills=["Python", "React"],
            preferred_skills=["AWS", "Docker"]
        )
        
        # Required: 100 * 0.7 = 70
        # Preferred: 100 * 0.3 = 30
        # Total: 100
        assert result["overall_score"] == 100
        assert result["preferred_match_score"] == 100
    
    def test_depth_bonus(self):
        """Test that extra skills provide depth bonus."""
        result = calculate_skill_match(
            candidate_skills=["Python", "React", "AWS", "Docker", "Kubernetes", "Go", "Rust"],
            required_skills=["Python", "React"],
            preferred_skills=["AWS"]
        )
        
        # 7 skills - 3 requirements = 4 extra skills
        # Depth bonus: min(10, 4 * 2) = 8
        assert result["depth_bonus"] > 0
        assert result["overall_score"] > 100 - 10  # Should get bonus
    
    def test_no_match(self):
        """Test completely mismatched skills."""
        result = calculate_skill_match(
            candidate_skills=["Java", "C++", "C#"],
            required_skills=["Python", "JavaScript", "Go"],
            preferred_skills=[]
        )
        
        assert result["required_match_score"] == 0
        assert len(result["matched_required"]) == 0
        assert len(result["missing_required"]) == 3


class TestExperienceScore:
    """Test experience scoring algorithm."""
    
    def test_perfect_match(self):
        """Test exact experience match."""
        result = calculate_experience_score(
            candidate_years=5.0,
            required_years=5.0,
            role_level="mid"
        )
        
        assert result["score"] == 100
        assert result["gap_years"] == 0
        assert result["meets_minimum"]
    
    def test_overqualified_moderate(self):
        """Test moderately overqualified candidate."""
        result = calculate_experience_score(
            candidate_years=8.0,
            required_years=5.0,
            role_level="mid"
        )
        
        # Excess ratio: 8/5 = 1.6 (between 1.5 and 2.0)
        assert result["score"] >= 90
        assert result["meets_minimum"]
    
    def test_overqualified_extreme(self):
        """Test significantly overqualified candidate (potential retention risk)."""
        result = calculate_experience_score(
            candidate_years=15.0,
            required_years=5.0,
            role_level="mid"
        )
        
        # Excess ratio: 15/5 = 3.0 (>= 2.0)
        assert result["score"] == 90  # Slight penalty
        assert result["penalty"] > 0
        assert "retention risk" in result["explanation"].lower()
    
    def test_within_gap_tolerance(self):
        """Test candidate with acceptable experience gap."""
        result = calculate_experience_score(
            candidate_years=4.0,
            required_years=5.0,
            role_level="mid",
            allow_gap=True,
            max_gap_years=1.0
        )
        
        assert result["score"] >= 60
        assert result["gap_years"] == 1.0
        assert result["meets_minimum"]
    
    def test_beyond_gap_tolerance(self):
        """Test candidate beyond acceptable gap."""
        result = calculate_experience_score(
            candidate_years=3.0,
            required_years=5.0,
            role_level="mid",
            allow_gap=True,
            max_gap_years=1.0
        )
        
        assert result["score"] < 80
        assert result["gap_years"] == 2.0
        assert not result["meets_minimum"]
    
    def test_gap_not_allowed(self):
        """Test strict experience requirement (no gap allowed)."""
        result = calculate_experience_score(
            candidate_years=4.0,
            required_years=5.0,
            role_level="senior",
            allow_gap=False
        )
        
        assert result["score"] < 100
        assert result["penalty"] > 0
        assert not result["meets_minimum"]
    
    def test_level_multiplier_junior(self):
        """Test that junior roles are more lenient."""
        result_junior = calculate_experience_score(
            candidate_years=1.0,
            required_years=2.0,
            role_level="junior",
            allow_gap=True,
            max_gap_years=1.0
        )
        
        result_senior = calculate_experience_score(
            candidate_years=6.0,
            required_years=7.0,
            role_level="senior",
            allow_gap=True,
            max_gap_years=1.0
        )
        
        # Junior should have higher score than senior for same gap
        assert result_junior["score"] > result_senior["score"]


class TestEducationScore:
    """Test education scoring algorithm."""
    
    def test_exact_match(self):
        """Test exact education match."""
        result = calculate_education_score(
            candidate_education="BS Computer Science",
            required_education="BS Computer Science"
        )
        
        assert result["score"] == 100
        assert result["difference"] == 0
        assert result["meets_requirement"]
    
    def test_exceeds_by_one_level(self):
        """Test candidate with one level higher education."""
        result = calculate_education_score(
            candidate_education="MS Computer Science",
            required_education="BS Computer Science"
        )
        
        assert result["score"] == 100
        assert result["difference"] == 1
        assert result["meets_requirement"]
    
    def test_significantly_exceeds(self):
        """Test PhD for BS requirement."""
        result = calculate_education_score(
            candidate_education="PhD Computer Science",
            required_education="BS Computer Science"
        )
        
        assert result["score"] == 95
        assert result["difference"] == 2
        assert result["meets_requirement"]
    
    def test_below_with_equivalent(self):
        """Test below requirement but 'equivalent' is mentioned."""
        result = calculate_education_score(
            candidate_education="Bootcamp Graduate",
            required_education="BS Computer Science or equivalent"
        )
        
        assert result["score"] >= 70
        # Should be more lenient due to "equivalent"
    
    def test_below_strict_requirement(self):
        """Test below strict requirement."""
        result = calculate_education_score(
            candidate_education="Associate Degree",
            required_education="BS Computer Science"
        )
        
        assert result["score"] < 80
        assert result["difference"] < 0
        assert not result["meets_requirement"]


class TestOverallScore:
    """Test overall score calculation."""
    
    def test_perfect_candidate(self):
        """Test candidate who is perfect fit."""
        candidate = CandidateProfile(
            candidate_id="TEST-001",
            name="Perfect Candidate",
            email="perfect@test.com",
            skills=["Python", "React", "AWS", "Docker"],
            experience_years=5.0,
            education="BS Computer Science",
            technical_interview_score=95.0,
            behavioral_interview_score=90.0,
            coding_challenge_score=92.0,
            salary_expectation=110000,
            work_preference="remote"
        )
        
        job = JobRequirements(
            job_id="JOB-001",
            title="Senior Software Engineer",
            department="Engineering",
            level="senior",
            required_skills=["Python", "React"],
            preferred_skills=["AWS", "Docker"],
            min_experience_years=5.0,
            required_education="BS Computer Science",
            budget_min=100000,
            budget_max=130000,
            work_mode="remote"
        )
        
        result = calculate_overall_score(candidate, job)
        
        assert result["overall_score"] >= 85
        assert result["recommendation"] in ["strong_hire", "hire"]
        assert len(result["key_factors"]["missing_required_skills"]) == 0
    
    def test_edge_case_candidate(self):
        """Test candidate with some issues."""
        candidate = CandidateProfile(
            candidate_id="TEST-002",
            name="Edge Case",
            email="edge@test.com",
            skills=["Python", "JavaScript"],  # Missing React
            experience_years=3.5,  # Below 5 years
            education="Bootcamp Graduate",  # Below BS
            technical_interview_score=70.0,
            behavioral_interview_score=75.0,
            coding_challenge_score=68.0,
            salary_expectation=110000,
            work_preference="remote"
        )
        
        job = JobRequirements(
            job_id="JOB-001",
            title="Senior Software Engineer",
            department="Engineering",
            level="senior",
            required_skills=["Python", "React", "AWS"],
            preferred_skills=["Docker"],
            min_experience_years=5.0,
            required_education="BS Computer Science",
            budget_min=100000,
            budget_max=130000,
            work_mode="remote"
        )
        
        result = calculate_overall_score(candidate, job, allow_experience_gap=True)
        
        assert result["overall_score"] < 85
        assert result["recommendation"] in ["conditional_hire", "reject"]
        assert len(result["key_factors"]["missing_required_skills"]) > 0
    
    def test_component_weights(self):
        """Test that component weights are applied correctly."""
        candidate = CandidateProfile(
            candidate_id="TEST-003",
            name="Test Candidate",
            email="test@test.com",
            skills=["Python"],
            experience_years=5.0,
            education="BS Computer Science",
            technical_interview_score=80.0,
            behavioral_interview_score=80.0,
            salary_expectation=100000,
            work_preference="remote"
        )
        
        job = JobRequirements(
            job_id="JOB-001",
            title="Software Engineer",
            department="Engineering",
            level="mid",
            required_skills=["Python"],
            min_experience_years=5.0,
            required_education="BS Computer Science",
            budget_min=90000,
            budget_max=120000,
            work_mode="remote"
        )
        
        result = calculate_overall_score(candidate, job)
        
        # Verify weights exist
        assert "weights" in result
        assert result["weights"]["skills"] == 0.40
        assert result["weights"]["experience"] == 0.30
        assert result["weights"]["education"] == 0.15
        assert result["weights"]["interviews"] == 0.15
        
        # Verify sum of weights = 1.0
        assert sum(result["weights"].values()) == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
