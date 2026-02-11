"""
Test: Hybrid Retrieval (Vector + Graph)

Demonstrates combining FAISS vector search with NetworkX graph traversal.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from tools.memory_query import get_memory_helper
from data.schemas import CandidateProfile, JobRequirements
import json

print("\n" + "="*80)
print("PHASE 5: HYBRID RETRIEVAL (VECTOR + GRAPH)")
print("="*80 + "\n")

# Load test data
with open("data/candidates.json") as f:
    candidates_data = json.load(f)
with open("data/job_requirements.json") as f:
    jobs_data = json.load(f)

candidate = CandidateProfile(**candidates_data[0])
job = JobRequirements(**jobs_data[0])

print(f"📋 Candidate: {candidate.name}")
print(f"📋 Job: {job.title}\n")

# Test 1: Standard RAG (vector only)
print("🔍 Test 1: Standard RAG (Vector Search Only)")
print("-" * 80)

memory_vector = get_memory_helper(use_hybrid=False)
results_vector = memory_vector.find_similar_hires(candidate, job, top_k=3)

if results_vector:
    print(f"Found {len(results_vector)} similar hires:")
    for i, hire in enumerate(results_vector, 1):
        print(f"   {i}. {hire['candidate_name']} - {hire['job_title']}")
        print(f"      Similarity: {hire.get('similarity', 0):.3f}")
else:
    print("   No results found")

print()

# Test 2: Hybrid Retrieval (vector + graph)
print("🔍 Test 2: Hybrid Retrieval (Vector + Graph)")
print("-" * 80)

memory_hybrid = get_memory_helper(use_hybrid=True)
results_hybrid = memory_hybrid.find_similar_hires(candidate, job, top_k=3)

if results_hybrid:
    print(f"Found {len(results_hybrid)} similar hires:")
    for i, hire in enumerate(results_hybrid, 1):
        print(f"   {i}. {hire['candidate_name']} - {hire['job_title']}")
        print(f"      Similarity: {hire.get('similarity', 0):.3f}")
        if 'graph_boost' in hire:
            print(f"      Graph Boost: +{hire['graph_boost']:.3f}")
else:
    print("   No results (hybrid may require graph data)")

print("\n" + "="*80)
print("📊 Result: Hybrid retrieval combines vector similarity + graph relationships!")
print("="*80 + "\n")

print("Benefits of Hybrid Retrieval:")
print("  ✅ Vector search: Semantic similarity")
print("  ✅ Graph traversal: Relationship-based relevance")
print("  ✅ Combined scoring: Best of both approaches")
print("  ✅ Richer context: Similar roles, skills, decisions\n")
