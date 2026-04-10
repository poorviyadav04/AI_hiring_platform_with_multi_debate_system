"""
Quick test to verify Phase 1: Memory integration is working.
Tests evaluation saving and retrieval.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from data.evaluation_store import get_evaluation_store
from data.schemas import CandidateProfile, JobRequirements, HiringConstraints
from agents.workflow import MultiAgentWorkflow
import json


def test_phase1_integration():
    """Test that evaluations are being saved to memory."""
    
    print("\n" + "="*70)
    print("PHASE 1 TEST: Memory Integration")
    print("="*70 + "\n")
    
    # Load test data
    with open("data/candidates.json") as f:
        candidates_data = json.load(f)
    with open("data/job_requirements.json") as f:
        jobs_data = json.load(f)
    with open("data/policies.json") as f:
        policies_data = json.load(f)
    
    # Create test candidate and job
    candidate = CandidateProfile(**candidates_data[0])
    job = JobRequirements(**jobs_data[0])
    constraints = HiringConstraints(**policies_data)
    
    print(f"Testing with:")
    print(f"  Candidate: {candidate.name} ({candidate.candidate_id})")
    print(f"  Job: {job.title} ({job.job_id})\n")
    
    # Get initial eval count
    eval_store = get_evaluation_store()
    stats_before = eval_store.get_statistics()
    print(f"Evaluations before: {stats_before['total_evaluations']}\n")
    
    #Run evaluation (this should save to memory)
    print("Running evaluation...")
    workflow = MultiAgentWorkflow(constraints=constraints, save_to_memory=True)
    result = workflow.run(candidate, job)
    
    # Check if evaluation was saved
    stats_after = eval_store.get_statistics()
    print(f"\nEvaluations after: {stats_after['total_evaluations']}")
    
    if stats_after['total_evaluations'] > stats_before['total_evaluations']:
        print("✅ PASS: Evaluation was saved to memory!\n")
        
        # Try to retrieve it
        candidate_history = eval_store.get_candidate_history(candidate.candidate_id)
        if candidate_history:
            latest = candidate_history[0]
            print("✅ PASS: Retrieved evaluation from memory")
            print(f"   Evaluation ID: {latest.evaluation_id}")
            print(f"   Score: {latest.overall_score:.1f}/100")
            print(f"   Decision: {latest.final_decision}")
            print(f"   Timestamp: {latest.timestamp}\n")
            
            # Verify debate transcript was saved
            if latest.debate_transcript and len(latest.debate_transcript) > 0:
                print(f"✅ PASS: Debate transcript saved ({len(latest.debate_transcript)} messages)\n")
            else:
                print("❌ FAIL: Debate transcript not saved\n")
                return False
            
            return True
        else:
            print("❌ FAIL: Could not retrieve evaluation from memory\n")
            return False
    else:
        print("❌ FAIL: Evaluation was not saved to memory\n")
        return False


def test_candidate_history():
    """Test retrieving candidate history."""
    
    print("="*70)
    print("TEST: Candidate History Retrieval")
    print("="*70 + "\n")
    
    eval_store = get_evaluation_store()
    
    # Get all evaluations
    all_evals = eval_store.get_all_evaluations(limit=5)
    
    if all_evals:
        print(f"✅ Found {len(all_evals)} recent evaluations\n")
        
        for i, eval in enumerate(all_evals, 1):
            print(f"{i}. {eval.candidate_name} → {eval.job_title}")
            print(f"   Score: {eval.overall_score:.1f}/100, Decision: {eval.final_decision}")
            print(f"   Date: {eval.timestamp[:10]}\n")
        
        # Test getting specific candidate history
        test_candidate_id = all_evals[0].candidate_id
        history = eval_store.get_candidate_history(test_candidate_id)
        
        print(f"History for {test_candidate_id}: {len(history)} evaluation(s)")
        if len(history) > 1:
            print("✅ PASS: Candidate has multiple evaluations tracked!\n")
        else:
            print("ℹ️  Candidate has 1 evaluation (expected for first test)\n")
        
        return True
    else:
        print("⚠️  No evaluations found yet (run an evaluation first)\n")
        return False


def test_statistics():
    """Test getting evaluation statistics."""
    
    print("="*70)
    print("TEST: Evaluation Statistics")
    print("="*70 + "\n")
    
    eval_store = get_evaluation_store()
    stats = eval_store.get_statistics()
    
    print(f"Total Evaluations: {stats['total_evaluations']}")
    print(f"Unique Candidates: {stats['unique_candidates']}")
    print(f"Unique Jobs: {stats['unique_jobs']}")
    print(f"Average Score: {stats['average_score']:.1f}/100")
    print(f"\nDecisions Breakdown:")
    for decision, count in stats['decisions'].items():
        print(f"  {decision}: {count}")
    
    print("\n✅ PASS: Statistics retrieved successfully\n")
    return True


if __name__ == "__main__":
    print("\n" + "#"*70)
    print("# PHASE 1 INTEGRATION TEST SUITE")
    print("#"*70)
    
    results = []
    
    # Test 1: Basic integration
    results.append(("Memory Integration", test_phase1_integration()))
    
    # Test 2: History retrieval
    results.append(("History Retrieval", test_candidate_history()))
    
    # Test 3: Statistics
    results.append(("Statistics", test_statistics()))
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed\n")
    
    if passed == total:
        print("🎉 Phase 1 Complete! Memory system is working.\n")
        exit(0)
    else:
        print("⚠️  Some tests failed. Review output above.\n")
        exit(1)
