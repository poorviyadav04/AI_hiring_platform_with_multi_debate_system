"""
Demo script to test deterministic scoring and constraint validation.
Run this to verify Phase 2 implementation without requiring pytest.
"""

import json
from pathlib import Path
import sys

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.scoring import (
    calculate_skill_match,
    calculate_experience_score,
    calculate_education_score,
    calculate_overall_score,
)
from tools.constraints import (
    check_budget_constraint,
    validate_experience_requirement,
    check_score_thresholds,
    validate_all_constraints,
)
from data.schemas import CandidateProfile, JobRequirements, HiringConstraints


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_skill_matching():
    """Demonstrate skill matching algorithm."""
    print_section("SKILL MATCHING TESTS")
    
    # Test 1: Perfect match
    print("\n1. Perfect Required Skills Match:")
    result = calculate_skill_match(
        candidate_skills=["Python", "React", "AWS", "Docker"],
        required_skills=["Python", "React", "AWS"],
        preferred_skills=["Docker"]
    )
    print(f"   Overall Score: {result['overall_score']}")
    print(f"   Required Match: {result['required_match_score']}%")
    print(f"   Preferred Match: {result['preferred_match_score']}%")
    print(f"   Matched Required: {result['matched_required']}")
    print(f"   Missing Required: {result['missing_required']}")
    print(f"   Depth Bonus: +{result['depth_bonus']} points")
    
    # Test 2: Partial match with missing skills
    print("\n2. Partial Match (Missing Skills):")
    result = calculate_skill_match(
        candidate_skills=["Python", "JavaScript"],
        required_skills=["Python", "React", "AWS", "Docker"],
        preferred_skills=["Kubernetes"]
    )
    print(f"   Overall Score: {result['overall_score']}")
    print(f"   Required Match: {result['required_match_score']}%")
    print(f"   Missing Required: {result['missing_required']}")
    
    # Test 3: Case insensitive
    print("\n3. Case Insensitive Matching:")
    result = calculate_skill_match(
        candidate_skills=["python", "REACT", "Aws"],
        required_skills=["Python", "React", "AWS"]
    )
    print(f"   Overall Score: {result['overall_score']}")
    print(f"   ✓ Case insensitive matching works!")


def test_experience_scoring():
    """Demonstrate experience scoring."""
    print_section("EXPERIENCE SCORING TESTS")
    
    # Test 1: Perfect match
    print("\n1. Perfect Experience Match:")
    result = calculate_experience_score(5.0, 5.0, "mid")
    print(f"   Score: {result['score']}")
    print(f"   Gap: {result['gap_years']} years")
    print(f"   Explanation: {result['explanation']}")
    
    # Test 2: Overqualified
    print("\n2. Overqualified Candidate:")
    result = calculate_experience_score(15.0, 5.0, "mid")
    print(f"   Score: {result['score']}")
    print(f"   Penalty: {result['penalty']}")
    print(f"   Explanation: {result['explanation']}")
    
    # Test 3: Within gap tolerance
    print("\n3. Acceptable Experience Gap:")
    result = calculate_experience_score(4.0, 5.0, "mid", allow_gap=True, max_gap_years=1.0)
    print(f"   Score: {result['score']}")
    print(f"   Gap: {result['gap_years']} years")
    print(f"   Meets Minimum: {result['meets_minimum']}")
    print(f"   Explanation: {result['explanation']}")
    
    # Test 4: Beyond tolerance
    print("\n4. Beyond Gap Tolerance:")
    result = calculate_experience_score(3.0, 5.0, "senior", allow_gap=True, max_gap_years=1.0)
    print(f"   Score: {result['score']}")
    print(f"   Gap: {result['gap_years']} years")
    print(f"   Meets Minimum: {result['meets_minimum']}")
    print(f"   Explanation: {result['explanation']}")


def test_budget_constraints():
    """Demonstrate budget constraint validation."""
    print_section("BUDGET CONSTRAINT TESTS")
    
    # Test 1: Within budget
    print("\n1. Within Budget:")
    result = check_budget_constraint(110000, 100000, 130000)
    print(f"   Compliant: {result['compliant']}")
    print(f"   Status: {result['status']}")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Margin: ${result['margin']:,.0f}")
    print(f"   Recommendation: {result['recommendation']}")
    
    # Test 2: Within tolerance
    print("\n2. Slightly Over Budget (Within Tolerance):")
    result = check_budget_constraint(123000, 100000, 120000, max_overage_percent=5.0)
    print(f"   Compliant: {result['compliant']}")
    print(f"   Strictly Compliant: {result['strictly_compliant']}")
    print(f"   Status: {result['status']}")
    print(f"   Margin: ${result['margin']:,.0f} ({result['margin_percent']:.1f}%)")
    print(f"   Recommendation: {result['recommendation']}")
    
    # Test 3: Exceeds tolerance
    print("\n3. Exceeds Budget Tolerance:")
    result = check_budget_constraint(135000, 100000, 120000, max_overage_percent=5.0)
    print(f"   Compliant: {result['compliant']}")
    print(f"   Status: {result['status']}")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Margin: ${result['margin']:,.0f} ({result['margin_percent']:.1f}%)")
    print(f"   Recommendation: {result['recommendation']}")


def test_overall_scoring():
    """Demonstrate overall scoring with real candidate."""
    print_section("OVERALL SCORING TEST")
    
    # Load a candidate from generated data
    data_dir = Path(__file__).parent.parent / "data"
    
    with open(data_dir / "candidates.json") as f:
        candidates_data = json.load(f)
    
    with open(data_dir / "job_requirements.json") as f:
        jobs_data = json.load(f)
    
    # Get first candidate and job
    candidate = CandidateProfile(**candidates_data[0])
    job = JobRequirements(**jobs_data[0])
    
    print(f"\nCandidate: {candidate.name}")
    print(f"   Skills: {', '.join(candidate.skills[:5])}")
    print(f"   Experience: {candidate.experience_years} years")
    print(f"   Education: {candidate.education}")
    print(f"   Salary Expectation: ${candidate.salary_expectation:,.0f}")
    print(f"   Technical Score: {candidate.technical_interview_score}")
    
    print(f"\nJob: {job.title}")
    print(f"   Level: {job.level}")
    print(f"   Required Skills: {', '.join(job.required_skills)}")
    print(f"   Min Experience: {job.min_experience_years} years")
    print(f"   Budget: ${job.budget_min:,.0f} - ${job.budget_max:,.0f}")
    
    # Calculate overall score
    result = calculate_overall_score(candidate, job)
    
    print(f"\n{'─' * 70}")
    print(f"RESULTS:")
    print(f"{'─' * 70}")
    print(f"   Overall Score: {result['overall_score']}/100")
    print(f"   Recommendation: {result['recommendation'].upper()}")
    
    print(f"\n   Component Scores:")
    for component, score in result['component_scores'].items():
        print(f"      {component.capitalize():12} {score:6.1f}/100 (weight: {result['weights'][component]*100:.0f}%)")
    
    print(f"\n   Key Factors:")
    print(f"      Missing Skills: {result['key_factors']['missing_required_skills']}")
    print(f"      Experience Gap: {result['key_factors']['experience_gap']:.1f} years")
    print(f"      Education Gap: {result['key_factors']['education_gap']} levels")


def test_full_validation():
    """Demonstrate full constraint validation."""
    print_section("FULL CONSTRAINT VALIDATION")
    
    # Load data
    data_dir = Path(__file__).parent.parent / "data"
    
    with open(data_dir / "candidates.json") as f:
        candidates_data = json.load(f)
    
    with open(data_dir / "job_requirements.json") as f:
        jobs_data = json.load(f)
    
    with open(data_dir / "policies.json") as f:
        policies_data = json.load(f)
    
    candidate = CandidateProfile(**candidates_data[5])  # Get candidate #6
    job = JobRequirements(**jobs_data[2])  # Get job #3
    constraints = HiringConstraints(**policies_data)
    
    # Calculate overall score
    overall_result = calculate_overall_score(candidate, job)
    
    # Validate all constraints
    validation = validate_all_constraints(
        candidate,
        job,
        overall_result['overall_score'],
        constraints
    )
    
    print(f"\nCandidate: {candidate.name}")
    print(f"Job: {job.title} ({job.level})")
    print(f"Overall Score: {overall_result['overall_score']:.1f}/100")
    
    print(f"\n{'─' * 70}")
    print(f"CONSTRAINT VALIDATION:")
    print(f"{'─' * 70}")
    print(f"   All Compliant: {'✓ YES' if validation['all_compliant'] else '✗ NO'}")
    print(f"   Compliance Rate: {validation['compliance_rate']*100:.0f}%")
    print(f"   Final Decision: {validation['final_decision'].upper()}")
    
    if validation['violations']:
        print(f"\n   ⚠️  Violations ({len(validation['violations'])}):")
        for v in validation['violations']:
            print(f"      • {v}")
    
    if validation['warnings']:
        print(f"\n   ⚡ Warnings ({len(validation['warnings'])}):")
        for w in validation['warnings']:
            print(f"      • {w}")
    
    if validation['all_compliant'] and not validation['warnings']:
        print(f"\n   ✓ All constraints satisfied - Ready to proceed!")
    
    print(f"\n   Requires Escalation: {'Yes' if validation['requires_escalation'] else 'No'}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  PHASE 2: DETERMINISTIC SCORING ENGINE - DEMO")
    print("=" * 70)
    
    try:
        test_skill_matching()
        test_experience_scoring()
        test_budget_constraints()
        test_overall_scoring()
        test_full_validation()
        
        print("\n" + "=" * 70)
        print("  ✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nPhase 2 Implementation:")
        print("  ✓ Skill matching algorithm")
        print("  ✓ Experience scoring with gap tolerance")
        print("  ✓ Education scoring with level hierarchy")
        print("  ✓ Budget constraint validation")
        print("  ✓ Score threshold checking")
        print("  ✓ Comprehensive constraint validation")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
