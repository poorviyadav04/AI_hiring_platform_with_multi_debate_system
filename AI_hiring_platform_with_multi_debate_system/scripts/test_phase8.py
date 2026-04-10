"""
Test script for Phase 8: Counterfactual Explanations.
"""

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from tools.counterfactuals import CounterfactualGenerator
from data.schemas import CandidateProfile, JobRequirements
from tools.scoring import calculate_overall_score


def test_counterfactuals():
    """Test counterfactual explanation generation."""
    print("\n" + "=" * 70)
    print("  PHASE 8: COUNTERFACTUAL EXPLANATIONS")
    print("=" * 70)
    
    # Load test data
    data_dir = Path(__file__).parent.parent / "data"
    
    with open(data_dir / "candidates.json") as f:
        candidates_data = json.load(f)
    with open(data_dir / "job_requirements.json") as f:
        jobs_data = json.load(f)
    
    candidate = CandidateProfile(**candidates_data[0])
    job = JobRequirements(**jobs_data[0])
    
    print(f"\nCandidate: {candidate.name}")
    print(f"Position: {job.title} ({job.level})")
    print("-" * 70)
    
    # Get current score
    current = calculate_overall_score(candidate, job)
    print(f"\nCurrent Overall Score: {current['overall_score']:.1f}/100")
    print(f"  Skills: {current['component_scores']['skills']:.0f}/100")
    print(f"  Experience: {current['component_scores']['experience']:.0f}/100")
    print(f"  Education: {current['component_scores']['education']:.0f}/100")
    
    # Initialize generator
    generator = CounterfactualGenerator()
    
    # Test 1: Skill Counterfactuals
    print("\n" + "=" * 70)
    print("  1️⃣  SKILL COUNTERFACTUALS")
    print("=" * 70)
    
    skill_cfs = generator.generate_skill_counterfactuals(candidate, job, top_k=5)
    
    if skill_cfs:
        print("\n💡 Top missing skills that would improve score:\n")
        for i, cf in enumerate(skill_cfs, 1):
            print(f"{i}. {cf['explanation']}")
            print(f"   Impact on skill score: +{cf['impact']:.1f} points\n")
    else:
        print("\n✅ Candidate has all required skills!")
    
    # Test 2: Experience Counterfactuals
    print("\n" + "=" * 70)
    print("  2️⃣  EXPERIENCE COUNTERFACTUALS")
    print("=" * 70)
    
    exp_cfs = generator.generate_experience_counterfactuals(candidate, job)
    
    print(f"\n📅 Current experience: {candidate.experience_years} years")
    print(f"   Required minimum: {job.min_experience_years} years\n")
    
    if exp_cfs:
        print("💡 How additional experience would help:\n")
        for i, cf in enumerate(exp_cfs[:3], 1):
            meets = "✅" if cf['meets_minimum'] else "⚠️"
            print(f"{i}. {cf['explanation']}")
            print(f"   {meets} Meets minimum requirement\n")
    
    # Test 3: Education Counterfactuals
    print("\n" + "=" * 70)
    print("  3️⃣  EDUCATION COUNTERFACTUALS")
    print("=" * 70)
    
    edu_cfs = generator.generate_education_counterfactuals(candidate, job)
    
    print(f"\n🎓 Current education: {candidate.education}")
    print(f"   Required: {job.required_education}\n")
    
    if edu_cfs:
        print("💡 How higher education would help:\n")
        for i, cf in enumerate(edu_cfs, 1):
            print(f"{i}. {cf['explanation']}\n")
    else:
        print("\n✅ Already at highest education level!")
    
    # Test 4: Salary Counterfactuals
    print("\n" + "=" * 70)
    print("  4️⃣  SALARY COUNTERFACTUALS")
    print("=" * 70)
    
    salary_cfs = generator.generate_salary_counterfactuals(candidate, job)
    
    print(f"\n💰 Current salary expectation: ${candidate.salary_expectation:,}")
    print(f"   Budget max: ${job.budget_max:,}\n")
    
    print("💡 Budget fit scenarios:\n")
    for i, cf in enumerate(salary_cfs[:3], 1):
        fit = "✅" if cf['within_budget'] else "❌"
        print(f"{i}. {cf['explanation']}")
        print(f"   {fit} Within budget\n")
    
    # Test 5: Overall Impact Analysis
    print("\n" + "=" * 70)
    print("  5️⃣  OVERALL IMPACT ANALYSIS")
    print("=" * 70)
    
    analysis = generator.generate_overall_counterfactuals(candidate, job, top_k=10)
    
    print(f"\nCurrent Overall Score: {analysis['current_overall_score']:.1f}/100\n")
    print("🎯 Top 5 ways to improve OVERALL score:\n")
    
    for i, cf in enumerate(analysis['counterfactuals'][:5], 1):
        print(f"{i}. {cf['change']}")
        print(f"   Overall: {cf['overall_current']:.1f} → {cf['overall_new']:.1f} (+{cf['overall_impact']:.1f} points)")
        print(f"   Component: {cf['current_score']:.1f} → {cf['new_score']:.1f} (+{cf['impact']:.1f} in {cf['type']})\n")
    
    # Test 6: Actionable Feedback
    print("\n" + "=" * 70)
    print("  6️⃣  ACTIONABLE FEEDBACK")
    print("=" * 70)
    
    feedback = generator.get_actionable_feedback(candidate, job, score_threshold=85.0)
    
    print("\n📋 Feedback to reach 85/100:\n")
    for line in feedback:
        print(line)
    
    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    
    summary = analysis['summary']
    print(f"\nTotal scenarios analyzed: {summary['total_scenarios']}")
    print(f"Actionable improvements: {summary['actionable_count']}")
    
    if summary['highest_impact']:
        hi = summary['highest_impact']
        print(f"\n🏆 Highest impact change:")
        print(f"   {hi['change']}")
        print(f"   Impact: +{hi['overall_impact']:.1f} points overall")
    
    print("\n" + "=" * 70)


def main():
    """Run Phase 8 testing."""
    try:
        test_counterfactuals()
        
        print("\n\n" + "=" * 70)
        print("  ✅ PHASE 8 TESTING COMPLETE")
        print("=" * 70)
        print("\nCounterfactual Explanations Features:")
        print("  ✓ Skill gap analysis")
        print("  ✓ Experience impact scenarios")
        print("  ✓ Education upgrade analysis")
        print("  ✓ Salary negotiation insights")
        print("  ✓ Overall score optimization")
        print("  ✓ Actionable feedback generation")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
