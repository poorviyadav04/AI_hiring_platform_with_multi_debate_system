"""
Complete end-to-end integration demo showcasing all system components.

This demonstrates:
1. RAG system (vector + graph)
2. Memory tools
3. Multi-agent debate
4. Decision tracking
"""

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from agents.workflow import MultiAgentWorkflow
from rag import VectorStore, DecisionGraph
from rag.hybrid_retrieval import HybridRetriever
from mcp_servers.memory_tools import initialize_memory_tools, MEMORY_TOOLS
from data.schemas import CandidateProfile, JobRequirements, HiringConstraints


def setup_system():
    """Initialize all system components."""
    print("\n" + "=" * 70)
    print("  INITIALIZING LLM DECISION INTELLIGENCE SYSTEM")
    print("=" * 70)
    
    data_dir = Path(__file__).parent.parent / "data"
    
    # Load data
    print("\n1. Loading data...")
    with open(data_dir / "candidates.json") as f:
        candidates_data = json.load(f)
    with open(data_dir / "job_requirements.json") as f:
        jobs_data = json.load(f)
    with open(data_dir / "policies.json") as f:
        policies_data = json.load(f)
    
    candidates = [CandidateProfile(**c) for c in candidates_data[:20]]  # Use subset for demo
    jobs = [JobRequirements(**j) for j in jobs_data[:5]]
    constraints = HiringConstraints(**policies_data)
    
    print(f"   ✓ Loaded {len(candidates)} candidates, {len(jobs)} jobs")
    
    # Initialize RAG system
    print("\n2. Initializing RAG system...")
    vector_store = VectorStore()
    
    # Try to load existing indices
    try:
        vector_store.load()
        print("   ✓ Loaded existing FAISS indices")
    except:
        print("   Building new indices...")
        vector_store.index_candidates(candidates)
        vector_store.index_jobs(jobs)
        vector_store.save()
        print("   ✓ Built and saved indices")
    
    # Initialize decision graph
    decision_graph = DecisionGraph()
    try:
        decision_graph.load()
        print("   ✓ Loaded existing decision graph")
    except:
        print("   Building new graph...")
        for c in candidates:
            decision_graph.add_candidate(c)
        for j in jobs:
            decision_graph.add_job(j)
        decision_graph.save()
        print("   ✓ Built and saved graph")
    
    # Initialize hybrid retriever
    hybrid_retriever = HybridRetriever(vector_store, decision_graph)
    print("   ✓ Hybrid retriever ready")
    
    # Initialize memory tools
    initialize_memory_tools(vector_store, decision_graph)
    print("   ✓ Memory tools initialized")
    
    # Initialize multi-agent workflow
    workflow = MultiAgentWorkflow(constraints=constraints)
    print("   ✓ Multi-agent workflow ready")
    
    print("\n" + "=" * 70)
    print("  ✅ SYSTEM INITIALIZATION COMPLETE")
    print("=" * 70)
    
    return {
        'candidates': candidates,
        'jobs': jobs,
        'constraints': constraints,
        'vector_store': vector_store,
        'decision_graph': decision_graph,
        'hybrid_retriever': hybrid_retriever,
        'workflow': workflow
    }


def demo_rag_retrieval(system):
    """Demo: RAG-based candidate retrieval."""
    print("\n\n" + "=" * 70)
    print("  DEMO 1: INTELLIGENT CANDIDATE RETRIEVAL (RAG)")
    print("=" * 70)
    
    query = "Senior Python engineer with cloud and database experience"
    print(f"\nQuery: '{query}'")
    print("-" * 70)
    
    # Vector search
    print("\n📊 Vector Similarity Search:")
    results = system['vector_store'].search_similar_candidates(query, top_k=3)
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['name']} - Similarity: {r['similarity_score']:.1%}")
        print(f"   Skills: {', '.join(r['skills'][:5])}")
        print(f"   Experience: {r['experience_years']} years")
    
    # Hybrid search
    print("\n🔄 Hybrid Search (Vector + Graph):")
    hybrid_results = system['hybrid_retriever'].retrieve_similar_candidates(query, top_k=3)
    for i, r in enumerate(hybrid_results, 1):
        print(f"{i}. {r['name']} - Similarity: {r['similarity_score']:.1%}")
        if 'graph_context' in r:
            ctx = r['graph_context']
            print(f"   History: {ctx['num_applications']} applications, {len(ctx['similar_candidates'])} similar")


def demo_memory_tools(system):
    """Demo: Memory tools for agents."""
    print("\n\n" + "=" * 70)
    print("  DEMO 2: MEMORY TOOLS")
    print("=" * 70)
    
    print("\n🔍 Testing: find_similar_candidates_tool")
    print("-" * 70)
    
    from mcp_servers.memory_tools import find_similar_candidates_tool
    
    result = find_similar_candidates_tool.invoke({
        'query': 'Machine learning engineer with Python',
        'top_k': 3
    })
    
    print(result[:800])  # Show first 800 chars
    print("... [output truncated]")


def demo_multi_agent_debate(system):
    """Demo: Complete multi-agent hiring evaluation."""
    print("\n\n" + "=" * 70)
    print("  DEMO 3: MULTI-AGENT HIRING DEBATE")
    print("=" * 70)
    
    # Select candidate and job
    candidate = system['candidates'][0]
    job = system['jobs'][0]
    
    print(f"\nEvaluating: {candidate.name}")
    print(f"Position: {job.title} ({job.level})")
    print("-" * 70)
    
    # Run workflow
    result = system['workflow'].run(candidate, job)
    
    # Show compact summary
    print("\n📋 DEBATE SUMMARY:")
    print("=" * 70)
    
    for msg in result['debate_transcript']:
        role_emoji = {
            'evaluator': '📊',
            'advocate': '👍',
            'skeptic': '🤔',
            'moderator': '⚖️'
        }
        emoji = role_emoji.get(msg['role'], '•')
        
        print(f"\n{emoji} {msg['agent'].upper()}")
        print("-" * 70)
        
        # Show first 400 and last 200 chars
        content = msg['content']
        if len(content) > 600:
            print(content[:400])
            print("\n... [truncated] ...\n")
            print(content[-200:])
        else:
            print(content)
    
    print("\n" + "=" * 70)
    print(f"FINAL DECISION: {result['final_decision'].upper()}")
    print(f"OVERALL SCORE: {result['overall_score']:.1f}/100")
    print("=" * 70)
    
    # Store decision in graph
    decision_obj = system['workflow'].create_decision_object(result)
    system['decision_graph'].add_decision(
        decision_obj,
        candidate.candidate_id,
        job.job_id
    )
    print(f"\n✓ Decision stored in graph: {decision_obj.decision_id}")
    
    return result


def demo_full_pipeline(system):
    """Demo: Complete hiring pipeline."""
    print("\n\n" + "=" * 70)
    print("  DEMO 4: COMPLETE HIRING PIPELINE")
    print("=" * 70)
    
    job = system['jobs'][1]  # Mid-level position
    print(f"\nHiring for: {job.title}")
    print(f"Department: {job.department}")
    print(f"Level: {job.level}")
    print("-" * 70)
    
    # Step 1: Find candidates using RAG
    print("\nSTEP 1: Finding candidates via RAG...")
    candidates = system['hybrid_retriever'].retrieve_candidates_for_job(job, top_k=5)
    print(f"Found {len(candidates)} candidates")
    
    for i, c in enumerate(candidates[:3], 1):
        print(f"  {i}. {c['name']} - {c['similarity_score']:.1%} match")
    
    # Step 2: Evaluate top 2 candidates
    print("\nSTEP 2: Multi-agent evaluation of top 2 candidates...")
    
    decisions = []
    for i in range(min(2, len(candidates))):
        candidate_id = candidates[i]['candidate_id']
        candidate = next(c for c in system['candidates'] if c.candidate_id == candidate_id)
        
        print(f"\n  Evaluating: {candidate.name}")
        result = system['workflow'].run(candidate, job)
        decisions.append(result)
        
        # Store decision
        decision_obj = system['workflow'].create_decision_object(result)
        system['decision_graph'].add_decision(decision_obj, candidate.candidate_id, job.job_id)
    
    # Step 3: Compare and recommend
    print("\nSTEP 3: Final recommendation...")
    print("=" * 70)
    
    for i, decision in enumerate(decisions, 1):
        print(f"\n{i}. {decision['candidate_name']}")
        print(f"   Decision: {decision['final_decision'].upper()}")
        print(f"   Score: {decision['overall_score']:.1f}/100")
    
    # Pick best
    best = max(decisions, key=lambda d: d['overall_score'])
    print(f"\n🏆 RECOMMENDED HIRE: {best['candidate_name']}")
    print(f"   Score: {best['overall_score']:.1f}/100")
    print(f"   Decision: {best['final_decision'].upper()}")
    
    # Save updated graph
    system['decision_graph'].save()
    print("\n✓ All decisions saved to graph")


def print_system_stats(system):
    """Print system statistics."""
    print("\n\n" + "=" * 70)
    print("  SYSTEM STATISTICS")
    print("=" * 70)
    
    # Graph stats
    stats = system['decision_graph'].get_statistics()
    print("\nDecision Graph:")
    print(f"  Nodes: {stats['total_nodes']} ({stats['candidates']} candidates, {stats['jobs']} jobs)")
    print(f"  Edges: {stats['total_edges']}")
    print(f"  Decisions: {stats['decisions']}")
    
    # Vector store
    print("\nVector Store:")
    print(f"  Candidates indexed: {len(system['vector_store'].candidate_metadata)}")
    print(f"  Jobs indexed: {len(system['vector_store'].job_metadata)}")


def main():
    """Run complete end-to-end demo."""
    print("\n" + "#" * 70)
    print("  LLM DECISION INTELLIGENCE SYSTEM - COMPLETE DEMO")
    print("#" * 70)
    
    try:
        # Setup system
        system = setup_system()
        
        # Run demos
        demo_rag_retrieval(system)
        demo_memory_tools(system)
        demo_multi_agent_debate(system)
        demo_full_pipeline(system)
        
        # Stats
        print_system_stats(system)
        
        print("\n\n" + "=" * 70)
        print("  ✅ COMPLETE DEMO FINISHED SUCCESSFULLY")
        print("=" * 70)
        print("\nAll System Components Validated:")
        print("  ✓ RAG System (Vector + Graph)")
        print("  ✓ Memory Tools")
        print("  ✓ Multi-Agent Debate")
        print("  ✓ Decision Tracking")
        print("  ✓ Complete Hiring Pipeline")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
