"""
Test execution tracer integration.
Verifies that traces are generated and saved correctly.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from data.schemas import CandidateProfile, JobRequirements
from agents.workflow import MultiAgentWorkflow
import json


def test_execution_trace():
    """Test that execution traces are generated."""
    
    print("\n" + "="*70)
    print("TEST: Execution Tracer Integration")
    print("="*70 + "\n")
    
    # Load test data
    with open("data/candidates.json") as f:
        candidates_data = json.load(f)
    with open("data/job_requirements.json") as f:
        jobs_data = json.load(f)
    
    candidate = CandidateProfile(**candidates_data[0])
    job = JobRequirements(**jobs_data[0])
    
    # Run workflow (should generate trace)
    workflow = MultiAgentWorkflow(save_to_memory=True)
    result = workflow.run(candidate, job)
    
    # Check if trace exists
    trace_dir = Path("data/traces")
    trace_files = list(trace_dir.rglob("*-trace.json"))
    
    if not trace_files:
        print("❌ FAIL: No trace files found\n")
        return False
    
    # Load most recent trace
    latest_trace = max(trace_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_trace) as f:
        trace_data = json.load(f)
    
    # Validate trace structure
    required_fields = ['evaluation_id', 'start_time', 'end_time', 'summary', 'events']
    for field in required_fields:
        if field not in trace_data:
            print(f"❌ FAIL: Missing field '{field}' in trace\n")
            return False
    
    # Check events
    events = trace_data['events']
    if len(events) == 0:
        print("❌ FAIL: No events logged\n")
        return False
    
    # Check for agent events
    agent_events = [e for e in events if e['event_type'] in ['agent_start', 'agent_end']]
    if len(agent_events) < 8:  # 4 agents * 2 events each
        print(f"⚠️  WARNING: Expected at least 8 agent events, got {len(agent_events)}\n")
    
    #  Check summary
    summary = trace_data['summary']
    if 'total_duration_ms' not in summary:
        print("❌ FAIL: Missing total_duration_ms in summary\n")
        return False
    
    print(f"✅ PASS: Execution trace generated successfully")
    print(f"   File: {latest_trace}")
    print(f"   Events: {len(events)}")
    print(f"   Duration: {summary['total_duration_ms']:.2f}ms")
    print(f"   Agents traced: {len(summary.get('agent_durations_ms', {}))}\n")
    
    # Print sample events
    print("Sample Events:")
    for event in events[:5]:
        print(f"  [{event['timestamp']}] {event['event_type']}: {event['action']} ({event['agent']})")
    print()
    
    return True


if __name__ == "__main__":
    result = test_execution_trace()
    
    if result:
        print("🎉 Phase 1 Complete! Execution tracing is working.\n")
        exit(0)
    else:
        print("⚠️  Test failed. Review output above.\n")
        exit(1)
