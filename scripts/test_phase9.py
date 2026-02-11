"""
Test script for Phase 9: Red Team Agent.
"""

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from agents.workflow import MultiAgentWorkflow
from agents.redteam_agent import RedTeamAgent
from data.schemas import CandidateProfile, JobRequirements, HiringConstraints
from utils.llm_client import get_llm_client


def test_redteam_basic():
    """Test Red Team agent on a normal decision."""
    print("\n" + "=" * 70)
    print("  PHASE 9: RED TEAM AGENT - BASIC TEST")
    print("=" * 70)
    
    # Load test data
    data_dir = Path(__file__).parent.parent / "data"
    
    with open(data_dir / "candidates.json") as f:
        candidates_data = json.load(f)
    with open(data_dir / "job_requirements.json") as f:
        jobs_data = json.load(f)
    with open(data_dir / "policies.json") as f:
        policies_data = json.load(f)
    
    candidate = CandidateProfile(**candidates_data[0])
    job = JobRequirements(**jobs_data[0])
    constraints = HiringConstraints(**policies_data)
    
    print(f"\nCandidate: {candidate.name}")
    print(f"Position: {job.title}")
    print("-" * 70)
    
    # Run normal workflow
    workflow = MultiAgentWorkflow(constraints=constraints)
    result = workflow.run(candidate, job)
    
    print(f"\nNormal Decision: {result['final_decision'].upper()}")
    print(f"Overall Score: {result['overall_score']:.1f}/100")
    
    # Now add Red Team challenge
    print("\n" + "=" * 70)
    print("  RED TEAM CHALLENGE")
    print("=" * 70)
    
    redteam = RedTeamAgent()
    
    # Create state from workflow result
    from agents.base_agent import AgentState
    state = AgentState(
        candidate=candidate,
        job=job,
        messages=[],
        scores=result['component_scores']
    )
    
    # Add workflow messages to state
    from agents.base_agent import AgentMessage
    from datetime import datetime
    for msg in result['debate_transcript']:
        agent_msg = AgentMessage(
            agent_name=msg['agent'],
            role=msg['role'],
            content=msg['content'],
            timestamp=datetime.now(),
            metadata=msg.get('metadata', {})
        )
        state.messages.append(agent_msg)
    
    # Set final decision
    state.final_decision = result['final_decision']
    
    # Run red team analysis
    state = redteam.run(state)
    
    # Display red team analysis
    redteam_msg = state.messages[-1]
    print("\n" + redteam_msg.content)
    
    return result, redteam_msg


def test_redteam_edge_cases():
    """Test Red Team on edge cases."""
    print("\n\n" + "=" * 70)
    print("  TESTING EDGE CASES")
    print("=" * 70)
    
    data_dir = Path(__file__).parent.parent / "data"
    
    with open(data_dir / "candidates.json") as f:
        candidates_data = json.load(f)
    with open(data_dir / "job_requirements.json") as f:
        jobs_data = json.load(f)
    with open(data_dir / "policies.json") as f:
        policies_data = json.load(f)
    
    constraints = HiringConstraints(**policies_data)
    workflow = MultiAgentWorkflow(constraints=constraints)
    redteam = RedTeamAgent()
    
    # Test different scenarios
    scenarios = [
        ("Boundary Score", candidates_data[5] if len(candidates_data) > 5 else candidates_data[0], jobs_data[1]),
        ("Overqualified", candidates_data[3] if len(candidates_data) > 3 else candidates_data[0], jobs_data[0]),
    ]
    
    for scenario_name, cand_data, job_data in scenarios:
        print(f"\n{'=' * 70}")
        print(f"  SCENARIO: {scenario_name}")
        print(f"{'=' * 70}")
        
        candidate = CandidateProfile(**cand_data)
        job = JobRequirements(**job_data)
        
        result = workflow.run(candidate, job)
        
        print(f"\nCandidate: {candidate.name}")
        print(f"Decision: {result['final_decision'].upper()}")
        print(f"Score: {result['overall_score']:.1f}/100")
        
        # Red team analysis
        from agents.base_agent import AgentState, AgentMessage
        state = AgentState(
            candidate=candidate,
            job=job,
            messages=[],
            scores=result['component_scores']
        )
        
        from datetime import datetime
        for msg in result['debate_transcript']:
            agent_msg = AgentMessage(
                agent_name=msg['agent'],
                role=msg['role'],
                content=msg['content'],
                timestamp=datetime.now(),
                metadata=msg.get('metadata', {})
            )
            state.messages.append(agent_msg)
        
        state.final_decision = result['final_decision']
        state = redteam.run(state)
        
        redteam_msg = state.messages[-1]
        challenges = redteam_msg.metadata.get('challenges_found', 0)
        
        print(f"\n🔍 Red Team Challenges: {challenges}")
        
        # Show first 500 chars of analysis
        content = redteam_msg.content
        if len(content) > 600:
            print(content[:400])
            print("\n... [truncated] ...\n")
            print(content[-200:])
        else:
            print(content)


def test_redteam_with_llm():
    """Test Red Team with LLM power."""
    print("\n\n" + "=" * 70)
    print("  LLM-POWERED RED TEAM")
    print("=" * 70)
    
    llm = get_llm_client()
    
    if llm.is_available():
        print("\n✅ Ollama detected - using LLM-powered Red Team")
    else:
        print("\n⚠️  Ollama not available - using deterministic Red Team")
    
    # Load data
    data_dir = Path(__file__).parent.parent / "data"
    
    with open(data_dir / "candidates.json") as f:
        candidates_data = json.load(f)
    with open(data_dir / "job_requirements.json") as f:
        jobs_data = json.load(f)
    with open(data_dir / "policies.json") as f:
        policies_data = json.load(f)
    
    candidate = CandidateProfile(**candidates_data[0])
    job = JobRequirements(**jobs_data[0])
    constraints = HiringConstraints(**policies_data)
    
    # Run workflow with LLM
    workflow = MultiAgentWorkflow(constraints=constraints)
    
    # Enable LLM for all agents
    workflow.advocate.llm = llm
    workflow.skeptic.llm = llm
    workflow.moderator.llm = llm
    
    result = workflow.run(candidate, job)
    
    print(f"\nCandidate: {candidate.name}")
    print(f"Decision: {result['final_decision'].upper()}")
    
    # Red team with LLM
    redteam = RedTeamAgent(llm=llm)
    
    from agents.base_agent import AgentState, AgentMessage
    state = AgentState(
        candidate=candidate,
        job=job,
        messages=[],
        scores=result['component_scores']
    )
    
    from datetime import datetime
    for msg in result['debate_transcript']:
        agent_msg = AgentMessage(
            agent_name=msg['agent'],
            role=msg['role'],
            content=msg['content'],
            timestamp=datetime.now(),
            metadata=msg.get('metadata', {})
        )
        state.messages.append(agent_msg)
    
    state.final_decision = result['final_decision']
    state = redteam.run(state)
    
    print("\n" + "=" * 70)
    print("  RED TEAM ANALYSIS (LLM)")
    print("=" * 70)
    print("\n" + state.messages[-1].content)


def main():
    """Run all Phase 9 tests."""
    try:
        # Test 1: Basic functionality
        test_redteam_basic()
        
        # Test 2: Edge cases
        test_redteam_edge_cases()
        
        # Test 3: LLM-powered (if available)
        test_redteam_with_llm()
        
        print("\n\n" + "=" * 70)
        print("  ✅ PHASE 9 TESTING COMPLETE")
        print("=" * 70)
        print("\nRed Team Agent Features:")
        print("  ✓ Bias detection")
        print("  ✓ Boundary condition testing")
        print("  ✓ Consistency validation")
        print("  ✓ Edge case identification")
        print("  ✓ Fairness verification")
        print("  ✓ Sensitivity analysis")
        print("  ✓ LLM-powered challenges (when available)")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
