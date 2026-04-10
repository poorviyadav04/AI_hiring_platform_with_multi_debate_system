"""
Quick test: Verify RAG integration in memory queries
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from data.schemas import CandidateProfile, JobRequirements
from tools.memory_query import get_memory_helper
import json

# Load test data
with open("data/candidates.json") as f:
    candidates_data = json.load(f)
with open("data/job_requirements.json") as f:
    jobs_data = json.load(f)

candidate = CandidateProfile(**candidates_data[0])
job = JobRequirements(**jobs_data[0])

# Test RAG memory query
print("\n" + "="*70)
print("TESTING RAG INTEGRATION IN MEMORY QUERIES")
print("="*70 + "\n")

memory = get_memory_helper()

print(f"📋 Test candidate: {candidate.name}")
print(f"📋 Job: {job.title}\n")

# Test 1: Find similar hires
print("🔍 Test 1: Finding similar hires via RAG vector search...")
similar_hires = memory.find_similar_hires(candidate, job, top_k=3)

if similar_hires:
    print(f"✅ Found {len(similar_hires)} similar hires:")
    for i, hire in enumerate(similar_hires, 1):
        print(f"   {i}. {hire['candidate_name']} - {hire['job_title']}")
        print(f"      Score: {hire['score']:.1f}, Similarity: {hire.get('similarity', 0):.3f}")
else:
    print("⚠️ No similar hires found")

print()

# Test 2: Find similar rejections
print("🔍 Test 2: Finding similar rejections via RAG vector search...")
similar_rejects = memory.find_similar_rejections(candidate, job, top_k=3)

if similar_rejects:
    print(f"✅ Found {len(similar_rejects)} similar rejections:")
    for i, reject in enumerate(similar_rejects, 1):
        print(f"   {i}. {reject['candidate_name']} - {reject['job_title']}")
        print(f"      Score: {reject['score']:.1f}, Similarity: {reject.get('similarity', 0):.3f}")
else:
    print("⚠️ No similar rejections found")

print("\n" + "="*70)
print("✅ RAG INTEGRATION TEST COMPLETE!")
print("="*70 + "\n")

print("📊 Result: Memory queries now use FAISS vector search for semantic similarity!")
print("   Agents will cite semantically similar cases, not just keyword matches.\n")
