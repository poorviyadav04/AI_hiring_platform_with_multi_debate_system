"""
Demo script to test multi-agent debate system.
"""

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from agents.workflow import MultiAgentWorkflow
from data.schemas import CandidateProfile, JobRequirements, HiringConstraints


def load_test_data():
    """Load test candidate and job."""
    data_dir = Path(__file__).parent.parent / "data"
    
    # Load candidates
    with open(data_dir / "candidates.json") as f:
        candidates_data = json.load(f)
    
    # Load jobs
    with open(data_dir / "job_requirements.json") as f:
        jobs_data = json.load(f)
    
    # Load policies
    with open(data_dir / "policies.json") as f:
        policies_data = json.load(f)
    
    return candidates_data, jobs_data, policies_data


def print_debate_message(message, show_full=False):
    """Print a formatted debate message."""
    role_emoji = {
        'evaluator': '📊',
        'advocate': '👍',
        'skeptic': '🤔',
        'moderator': '⚖️'
    }
    
    emoji = role_emoji.get(message['role'], '•')
    
    print(f"\n{emoji} {message['agent'].upper()} ({message['role']})")
    print("─" * 70)
    
    content = message['content']
    if not show_full and len(content) > 800:
        # Show first 400 and last 400 chars for long messages
        print(content[:400])
        print("\n... [content truncated] ...\n")
        print(content[-400:])
    else:
        print(content)


def test_multi_agent_debate():
    """Test multi-agent debate on sample candidates."""
    print("\n" + "=" * 70)
    print("  PHASE 5: MULTI-AGENT DEBATE SYSTEM - DEMO")
    print("=" * 70)
    
    # Load data
    print("\nLoading test data...")
    candidates_data, jobs_data, policies_data = load_test_data()
    
    constraints = HiringConstraints(**policies_data)
    
    # Initialize workflow
    workflow = MultiAgentWorkflow(constraints=constraints)
    
    # Test cases
    test_cases = [
        (0, 0, "Strong candidate for junior role"),
        (5, 2, "Mid-level candidate with some gaps"),
        (10, 4, "Senior role with overqualified candidate"),
    ]
    
    results = []
    
    for candidate_idx, job_idx, description in test_cases:
        print(f"\n\n{'#' * 70}")
        print(f"TEST CASE: {description}")
        print(f"{'#' * 70}")
        
        candidate = CandidateProfile(**candidates_data[candidate_idx])
        job = JobRequirements(**jobs_data[job_idx])
        
        # Run workflow
        result = workflow.run(candidate, job)
        results.append(result)
        
        # Print compact summary
        print("\nDEBATE SUMMARY:")
        print("=" * 70)
        
        # Show each agent's message
        for msg in result['debate_transcript']:
            print_debate_message(msg, show_full=False)
        
        print("\n" + "=" * 70)
        print(f"FINAL DECISION: {result['final_decision'].upper()}")
        print(f"OVERALL SCORE: {result['overall_score']:.1f}/100")
        print("=" * 70)
        
        # Pause between test cases
        if candidate_idx != test_cases[-1][0]:
            input("\nPress Enter to continue to next test case...")
    
    # Summary statistics
    print("\n\n" + "=" * 70)
    print("  SUMMARY STATISTICS")
    print("=" * 70)
    
    decision_counts = {}
    for r in results:
        decision = r['final_decision']
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
    
    print(f"\nTotal Evaluations: {len(results)}")
    print("\nDecision Breakdown:")
    for decision, count in decision_counts.items():
        print(f"  {decision.upper()}: {count}")
    
    avg_score = sum(r['overall_score'] for r in results) / len(results)
    print(f"\nAverage Score: {avg_score:.1f}/100")
    
    print("\n" + "=" * 70)
    print("  ✅ MULTI-AGENT TESTING COMPLETE")
    print("=" * 70)
    print("\nPhase 5 Implementation:")
    print("  ✓ 4 specialized agents (Evaluator, Advocate, Skeptic, Moderator)")
    print("  ✓ State management with message passing")
    print("  ✓ Sequential debate workflow")
    print("  ✓ Decision synthesis from multiple perspectives")
    print("\n" + "=" * 70)


def main():
    """Run multi-agent demo."""
    try:
        test_multi_agent_debate()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
