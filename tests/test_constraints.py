"""
Unit tests for constraint validation functions.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.constraints import (
    check_budget_constraint,
    validate_experience_requirement,
    check_score_thresholds,
    validate_all_constraints,
)
from data.schemas import CandidateProfile, JobRequirements, HiringConstraints


class TestBudgetConstraint:
    """Test budget constraint validation."""
    
    def test_within_budget(self):
        """Test salary within budget."""
        result = check_budget_constraint(
            candidate_salary=100000,
            job_budget_min=90000,
            job_budget_max=120000,
            max_overage_percent=5.0
        )
        
        assert result["compliant"]
        assert result["strictly_compliant"]
        assert result["status"] == "within_budget"
        assert result["risk_level"] == "low"
        assert result["recommendation"] == "approve"
    
    def test_under_budget(self):
        """Test salary below minimum (saves money)."""
        result = check_budget_constraint(
            candidate_salary=80000,
            job_budget_min=90000,
            job_budget_max=120000
        )
        
        assert result["compliant"]
        assert result["status"] == "under_budget"
        assert result["margin"] == 10000
        assert result["recommendation"] == "approve"
    
    def test_within_tolerance(self):
        """Test salary slightly over budget but within tolerance."""
        result = check_budget_constraint(
            candidate_salary=123000,  # 3K over $120K budget
            job_budget_min=90000,
            job_budget_max=120000,
            max_overage_percent=5.0  # Allows up to $126K
        )
        
        assert result["compliant"]
        assert not result["strictly_compliant"]
        assert result["status"] == "within_tolerance"
        assert result["risk_level"] == "medium"
        assert "negotiation" in result["recommendation"]
    
    def test_exceeds_tolerance(self):
        """Test salary beyond acceptable tolerance."""
        result = check_budget_constraint(
            candidate_salary=130000,
            job_budget_min=90000,
            job_budget_max=120000,
            max_overage_percent=5.0  # Max allowed: $126K
        )
        
        assert not result["compliant"]
        assert result["status"] == "exceeds_tolerance"
        assert result["risk_level"] == "high"
        assert "reject" in result["recommendation"].lower()
    
    def test_vp_approval_threshold(self):
        """Test that high salaries require VP approval."""
        result = check_budget_constraint(
            candidate_salary=160000,
            job_budget_min=150000,
            job_budget_max=180000
        )
        
        assert result["requires_vp_approval"]
    
    def test_margin_calculation(self):
        """Test margin calculations are accurate."""
        result = check_budget_constraint(
            candidate_salary=110000,
            job_budget_min=90000,
            job_budget_max=120000
        )
        
        expected_margin = 120000 - 110000
        assert result["margin"] == expected_margin
        assert result["margin_percent"] == pytest.approx((expected_margin / 120000) * 100, rel=0.01)


class TestExperienceRequirement:
    """Test experience requirement validation."""
    
    def test_meets_requirement(self):
        """Test candidate meets experience requirement."""
        result = validate_experience_requirement(
            candidate_years=5.0,
            required_years=5.0
        )
        
        assert result["compliant"]
        assert result["status"] == "meets_requirement"
        assert result["gap"] == 0
    
    def test_exceeds_requirement(self):
        """Test candidate exceeds requirement."""
        result = validate_experience_requirement(
            candidate_years=8.0,
            required_years=5.0
        )
        
        assert result["compliant"]
        assert result["status"] == "meets_requirement"
        assert result["gap"] < 0  # Negative gap = excess
    
    def test_within_gap_tolerance(self):
        """Test candidate within acceptable gap."""
        result = validate_experience_requirement(
            candidate_years=4.0,
            required_years=5.0,
            allow_gap=True,
            max_gap_years=1.0
        )
        
        assert result["compliant"]
        assert result["status"] == "within_gap_tolerance"
        assert result["gap"] == 1.0
    
    def test_exceeds_gap_tolerance(self):
        """Test candidate beyond acceptable gap."""
        result = validate_experience_requirement(
            candidate_years=3.0,
            required_years=5.0,
            allow_gap=True,
            max_gap_years=1.0
        )
        
        assert not result["compliant"]
        assert result["status"] == "below_requirement"
        assert result["gap"] == 2.0
    
    def test_gap_not_allowed(self):
        """Test when gaps are not allowed."""
        result = validate_experience_requirement(
            candidate_years=4.5,
            required_years=5.0,
            allow_gap=False
        )
        
        assert not result["compliant"]
        assert result["status"] == "below_requirement"


class TestScoreThresholds:
    """Test score threshold validation."""
    
    def test_all_scores_pass(self):
        """Test when all scores meet thresholds."""
        result = check_score_thresholds(
            technical_score=80.0,
            behavioral_score=75.0,
            overall_score=78.0,
            min_technical=60.0,
            min_behavioral=60.0,
            min_overall=65.0
        )
        
        assert result["compliant"]
        assert result["failure_count"] == 0
        assert len(result["failures"]) == 0
    
    def test_technical_score_fails(self):
        """Test technical score below threshold."""
        result = check_score_thresholds(
            technical_score=55.0,
            behavioral_score=75.0,
            overall_score=70.0,
            min_technical=60.0,
            min_behavioral=60.0,
            min_overall=65.0
        )
        
        assert not result["compliant"]
        assert result["failure_count"] == 1
        assert result["failures"][0]["type"] == "technical_score"
        assert result["failures"][0]["gap"] == 5.0
    
    def test_multiple_failures(self):
        """Test multiple score failures."""
        result = check_score_thresholds(
            technical_score=55.0,
            behavioral_score=58.0,
            overall_score=60.0,
            min_technical=60.0,
            min_behavioral=60.0,
            min_overall=65.0
        )
        
        assert not result["compliant"]
        assert result["failure_count"] == 3
        failure_types = [f["type"] for f in result["failures"]]
        assert "technical_score" in failure_types
        assert "behavioral_score" in failure_types
        assert "overall_score" in failure_types
    
    def test_none_scores_handled(self):
        """Test that None scores are handled gracefully."""
        result = check_score_thresholds(
            technical_score=None,
            behavioral_score=None,
            overall_score=70.0,
            min_technical=60.0,
            min_behavioral=60.0,
            min_overall=65.0
        )
        
        # Should only check overall score
        assert result["compliant"]
        assert "technical_score" not in [f["type"] for f in result["failures"]]


class TestValidateAllConstraints:
    """Test comprehensive constraint validation."""
    
    def test_all_constraints_pass(self):
        """Test candidate passing all constraints."""
        candidate = CandidateProfile(
            candidate_id="TEST-001",
            name="Good Candidate",
            email="good@test.com",
            skills=["Python", "React"],
            experience_years=5.0,
            education="BS Computer Science",
            technical_interview_score=80.0,
            behavioral_interview_score=75.0,
            salary_expectation=110000,
            work_preference="remote"
        )
        
        job = JobRequirements(
            job_id="JOB-001",
            title="Software Engineer",
            department="Engineering",
            level="mid",
            required_skills=["Python"],
            min_experience_years=4.0,
            required_education="BS Computer Science",
            budget_min=100000,
            budget_max=130000,
            work_mode="remote"
        )
        
        constraints = HiringConstraints(
            policy_id="POL-001",
            policy_name="Standard Policy",
            max_budget_overage_percent=5.0,
            allow_experience_gap=True,
            max_experience_gap_years=1.0,
            min_technical_score=60.0,
            min_behavioral_score=60.0,
            min_overall_score=65.0
        )
        
        result = validate_all_constraints(candidate, job, 75.0, constraints)
        
        assert result["all_compliant"]
        assert result["compliance_rate"] == 1.0
        assert result["final_decision"] == "approve"
        assert len(result["violations"]) == 0
    
    def test_budget_violation(self):
        """Test budget constraint violation."""
        candidate = CandidateProfile(
            candidate_id="TEST-002",
            name="Expensive Candidate",
            email="expensive@test.com",
            skills=["Python"],
            experience_years=5.0,
            education="BS Computer Science",
            technical_interview_score=80.0,
            behavioral_interview_score=75.0,
            salary_expectation=150000,  # Way over budget
            work_preference="remote"
        )
        
        job = JobRequirements(
            job_id="JOB-001",
            title="Software Engineer",
            department="Engineering",
            level="mid",
            required_skills=["Python"],
            min_experience_years=4.0,
            required_education="BS Computer Science",
            budget_min=100000,
            budget_max=120000,
            work_mode="remote"
        )
        
        constraints = HiringConstraints(
            policy_id="POL-001",
            policy_name="Standard Policy",
            min_technical_score=60.0,
            min_behavioral_score=60.0,
            min_overall_score=65.0
        )
        
        result = validate_all_constraints(candidate, job, 75.0, constraints)
        
        assert not result["all_compliant"]
        assert len(result["violations"]) > 0
        assert any("Budget" in v for v in result["violations"])
    
    def test_multiple_violations(self):
        """Test multiple constraint violations."""
        candidate = CandidateProfile(
            candidate_id="TEST-003",
            name="Problematic Candidate",
            email="problem@test.com",
            skills=["Python"],
            experience_years=2.0,  # Too little
            education="BS Computer Science",
            technical_interview_score=55.0,  # Too low
            behavioral_interview_score=58.0,  # Too low
            salary_expectation=140000,  # Too high
            work_preference="remote"
        )
        
        job = JobRequirements(
            job_id="JOB-001",
            title="Senior Engineer",
            department="Engineering",
            level="senior",
            required_skills=["Python"],
            min_experience_years=6.0,
            required_education="BS Computer Science",
            budget_min=100000,
            budget_max=120000,
            work_mode="remote"
        )
        
        constraints = HiringConstraints(
            policy_id="POL-001",
            policy_name="Standard Policy",
            allow_experience_gap=True,
            max_experience_gap_years=1.0,
            min_technical_score=60.0,
            min_behavioral_score=60.0,
            min_overall_score=65.0
        )
        
        result = validate_all_constraints(candidate, job, 60.0, constraints)
        
        assert not result["all_compliant"]
        assert len(result["violations"]) >= 3  # Budget, experience, scores
        assert result["final_decision"] == "reject"
    
    def test_warnings_vs_violations(self):
        """Test distinction between warnings and violations."""
        candidate = CandidateProfile(
            candidate_id="TEST-004",
            name="Warning Candidate",
            email="warning@test.com",
            skills=["Python"],
            experience_years=5.0,
            education="BS Computer Science",
            technical_interview_score=80.0,
            behavioral_interview_score=75.0,
            salary_expectation=124000,  # Slightly over, within tolerance
            work_preference="remote"
        )
        
        job = JobRequirements(
            job_id="JOB-001",
            title="Software Engineer",
            department="Engineering",
            level="mid",
            required_skills=["Python"],
            min_experience_years=4.0,
            required_education="BS Computer Science",
            budget_min=100000,
            budget_max=120000,
            work_mode="remote"
        )
        
        constraints = HiringConstraints(
            policy_id="POL-001",
            policy_name="Standard Policy",
            max_budget_overage_percent=5.0,
            min_technical_score=60.0,
            min_behavioral_score=60.0,
            min_overall_score=65.0
        )
        
        result = validate_all_constraints(candidate, job, 75.0, constraints)
        
        assert result["all_compliant"]  # Within tolerance
        assert len(result["warnings"]) > 0  # But has warnings
        assert len(result["violations"]) == 0
        assert result["final_decision"] == "conditional_approve"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
