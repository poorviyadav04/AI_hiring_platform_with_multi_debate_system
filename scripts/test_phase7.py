"""
Test script for LLM-powered multi-agent debate.
"""

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from agents.workflow import MultiAgentWorkflow
from data.schemas import CandidateProfile, JobRequirements, HiringConstraints
from utils.llm_client import get_llm_client


def check_ollama_status():
    """Check if Ollama is available."""
    print("\n" + "=" * 70)
    print("  CHECKING OLLAMA STATUS")
    print("=" * 70)
    
    llm = get_llm_client()
    
    if llm.is_available():
        print("✅ Ollama is running")
        models = llm.list_models()
        print(f"✅ Available models: {', '.join(models) if models else 'None'}")
        
        if not models:
            print("\n⚠️  WARNING: No models found!")
            print("   Run: ollama pull llama3")
            return False
        
        return True
    else:
        print("❌ Ollama is NOT running")
        print("\n📖 To start Ollama:")
        print("   1. Download from: https://ollama.ai")
        print("   2. Run: ollama serve")
        print("   3. In another terminal: ollama pull llama3")
        print("\n⚠️  Falling back to template-based responses...")
        return False


def test_llm_powered_debate():
    """Test LLM-powered multi-agent debate."""
    print("\n" + "=" * 70)
    print("  PHASE 7: LLM-POWERED MULTI-AGENT DEBATE")
    print("=" * 70)
    
    # Check Ollama
    ollama_available = check_ollama_status()
    
    # Load test data
    print("\nLoading test data...")
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
    
    print(f"✓ Testing with: {candidate.name} for {job.title}")
    
    # Initialize workflow with LLM support
    print("\nInitializing LLM-powered workflow...")
    workflow = MultiAgentWorkflow(constraints=constraints)
    
    # Enable LLM for agents
    from utils.llm_client import get_llm_client
    llm = get_llm_client()
    
    workflow.advocate.llm = llm
    workflow.skeptic.llm = llm
    workflow.moderator.llm = llm
    
    if ollama_available:
        print("✓ Agents configured with LLM (Ollama)")
    else:
        print("⚠️  Agents will use fallback mode (template-based)")
    
    # Run debate
    print("\n" + "=" * 70)
    print("  RUNNING LLM-POWERED DEBATE")
    print("=" * 70)
    
    result = workflow.run(candidate, job)
    
    # Display results
    print("\n" + "=" * 70)
    print("  DEBATE TRANSCRIPT")
    print("=" * 70)
    
    role_emoji = {
        'evaluator': '📊',
        'advocate': '👍',
        'skeptic': '🤔',
        'moderator': '⚖️'
    }
    
    for msg in result['debate_transcript']:
        emoji = role_emoji.get(msg['role'], '•')
        
        print(f"\n{emoji} {msg['agent'].upper()} ({msg['role']})")
        print("-" * 70)
        
        # Show full message for LLM-powered agents
        content = msg['content']
        if msg['role'] in ['advocate', 'skeptic', 'moderator'] and ollama_available:
            # Show full LLM-generated content
            print(content)
        else:
            # Show truncated for template-based
            if len(content) > 600:
                print(content[:400])
                print("\n... [truncated] ...\n")
                print(content[-200:])
            else:
                print(content)
    
    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"Final Decision: {result['final_decision'].upper()}")
    print(f"Overall Score: {result['overall_score']:.1f}/100")
    print(f"LLM Mode: {'ENABLED ✅' if ollama_available else 'FALLBACK ⚠️'}")
    print("=" * 70)
    
    if not ollama_available:
        print("\n💡 TIP: Install Ollama to see natural language debates!")
        print("   The system works with or without an LLM, but LLM makes it more dynamic.")


def main():
    """Run LLM integration test."""
    try:
        test_llm_powered_debate()
        
        print("\n\n" + "=" * 70)
        print("  ✅ PHASE 7 TESTING COMPLETE")
        print("=" * 70)
        print("\nLLM Integration Status:")
        print("  ✓ Ollama client wrapper created")
        print("  ✓ Agents updated with LLM support")
        print("  ✓ Fallback mode for offline usage")
        print("  ✓ Multi-agent debate tested")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
