"""
Script to build FAISS indices and decision graph from synthetic data.
Run this before using memory tools.
"""

import json
from pathlib import Path
import sys

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from rag import VectorStore, DecisionGraph
from data.schemas import CandidateProfile, JobRequirements


def load_data():
    """Load synthetic data."""
    data_dir = Path(__file__).parent.parent / "data"
    
    print("Loading synthetic data...")
    
    # Load candidates
    with open(data_dir / "candidates.json") as f:
        candidates_data = json.load(f)
    candidates = [CandidateProfile(**c) for c in candidates_data]
    
    # Load jobs
    with open(data_dir / "job_requirements.json") as f:
        jobs_data = json.load(f)
    jobs = [JobRequirements(**j) for j in jobs_data]
    
    print(f"✓ Loaded {len(candidates)} candidates and {len(jobs)} jobs")
    
    return candidates, jobs


def build_vector_store(candidates, jobs):
    """Build FAISS vector store."""
    print("\n" + "=" * 70)
    print("  BUILDING VECTOR STORE")
    print("=" * 70)
    
    vector_store = VectorStore()
    
    # Index candidates
    print("\nIndexing candidates...")
    vector_store.index_candidates(candidates)
    
    # Index jobs
    print("\nIndexing jobs...")
    vector_store.index_jobs(jobs)
    
    # Test search
    print("\n" + "-" * 70)
    print("Testing vector search...")
    results = vector_store.search_similar_candidates("Python developer with cloud experience", top_k=3)
    
    print(f"\nTop 3 results for 'Python developer with cloud experience':")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['name']} - Score: {result.get('similarity', 0):.2%}")
    
    # Save
    vector_store.save()
    
    return vector_store


def build_decision_graph(candidates, jobs):
    """Build NetworkX decision graph."""
    print("\n" + "=" * 70)
    print("  BUILDING DECISION GRAPH")
    print("=" * 70)
    
    graph = DecisionGraph()
    
    # Add all candidates as nodes
    print(f"\nAdding {len(candidates)} candidate nodes...")
    for candidate in candidates:
        graph.add_candidate(candidate)
    
    # Add all jobs as nodes
    print(f"Adding {len(jobs)} job nodes...")
    for job in jobs:
        graph.add_job(job)
    
    # Add some similarity edges (based on vector similarity for demo)
    print("\nAdding similarity edges...")
    
    # For demo: Connect candidates with similar skills
    from collections import defaultdict
    skill_groups = defaultdict(list)
    
    for candidate in candidates:
        # Group by primary skill
        if candidate.skills:
            primary_skill = candidate.skills[0]
            skill_groups[primary_skill].append(candidate.candidate_id)
    
    edges_added = 0
    for skill, candidate_ids in skill_groups.items():
        if len(candidate_ids) > 1:
            # Connect first few candidates in each skill group
            for i in range(min(3, len(candidate_ids))):
                for j in range(i + 1, min(3, len(candidate_ids))):
                    graph.add_similarity_edge(
                        candidate_ids[i],
                        candidate_ids[j],
                        similarity_score=0.8  # Demo value
                    )
                    edges_added += 1
    
    print(f"✓ Added {edges_added} similarity edges")
    
    # Get statistics
    stats = graph.get_statistics()
    print("\nGraph Statistics:")
    print(f"  Total Nodes: {stats['total_nodes']}")
    print(f"  Total Edges: {stats['total_edges']}")
    print(f"  Candidates: {stats['candidates']}")
    print(f"  Jobs: {stats['jobs']}")
    
    # Save
    graph.save()
    
    return graph


def test_hybrid_retrieval(vector_store, graph):
    """Test hybrid retrieval."""
    print("\n" + "=" * 70)
    print("  TESTING HYBRID RETRIEVAL")
    print("=" * 70)
    
    from rag.hybrid_retrieval import HybridRetriever
    
    retriever = HybridRetriever(vector_store, graph)
    
    # Test query
    query = "Senior Python engineer with AWS experience"
    print(f"\nQuery: '{query}'")
    print("-" * 70)
    
    results = retriever.retrieve_similar_candidates(query, top_k=5)
    
    print(f"\nTop 5 Candidates:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['name']} (ID: {result['candidate_id']})")
        print(f"   Similarity: {result.get('similarity', 0):.1%}")
        print(f"   Skills: {', '.join(result['skills'][:5])}")
        print(f"   Experience: {result['experience_years']} years")
        
        if 'graph_context' in result:
            ctx = result['graph_context']
            print(f"   Graph Context: {ctx['num_applications']} applications, {len(ctx['similar_candidates'])} similar candidates")


def main():
    """Main execution."""
    print("\n" + "=" * 70)
    print("  PHASE 4: BUILDING RAG SYSTEM")
    print("=" * 70)
    
    try:
        # Load data
        candidates, jobs = load_data()
        
        # Build vector store
        vector_store = build_vector_store(candidates, jobs)
        
        # Build decision graph  
        graph = build_decision_graph(candidates, jobs)
        
        # Test hybrid retrieval
        test_hybrid_retrieval(vector_store, graph)
        
        print("\n" + "=" * 70)
        print("  ✅ RAG SYSTEM BUILT SUCCESSFULLY!")
        print("=" * 70)
        print("\nCreated:")
        print("  ✓ FAISS vector indices (candidates + jobs)")
        print("  ✓ NetworkX decision graph")
        print("  ✓ Hybrid retrieval system")
        print("\nNext: Use memory tools in agents!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
