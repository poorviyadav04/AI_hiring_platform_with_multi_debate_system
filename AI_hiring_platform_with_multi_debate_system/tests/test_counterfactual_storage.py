"""
Test: Generate and store counterfactuals in vector database
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from data.schemas import CandidateProfile, JobRequirements
from tools.counterfactuals import CounterfactualGenerator
from rag.vector_store import VectorStore
import json

print("\n" + "="*80)
print("PHASE 3: COUNTERFACTUAL STORAGE IN VECTOR DB")
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

# Step 1: Generate counterfactuals
print("🔨 Step 1: Generating counterfactuals...")
cf_gen = CounterfactualGenerator()
analysis = cf_gen.generate_overall_counterfactuals(candidate, job, top_k=10)

print(f"✅ Generated {len(analysis['counterfactuals'])} counterfactuals\n")

# Step 2: Prepare for storage
print("💾 Step 2: Preparing counterfactuals for storage...")
counterfactuals_to_store = []
for cf in analysis['counterfactuals']:
    cf_record = {
        'candidate_id': candidate.candidate_id,
        'candidate_name': candidate.name,
        'job_title': job.title,
        **cf  # Include all counterfactual data
    }
    counterfactuals_to_store.append(cf_record)

print(f"✅ Prepared {len(counterfactuals_to_store)} records\n")

# Step 3: Index in vector store
print("🔍 Step 3: Indexing counterfactuals in FAISS vector store...")
vector_store = VectorStore()

# Try to load existing index
try:
    vector_store.load()
except Exception as e:
    print(f"⚠️ No existing index: {e}")

# Index new counterfactuals
vector_store.index_counterfactuals(counterfactuals_to_store)

# Save
vector_store.save()
print()

# Step 4: Test semantic search
print("🔎 Step 4: Testing semantic search for counterfactuals...")
print()

test_queries = [
    "How to improve Python skills?",
    "What if candidate had more experience?",
    "Ways to increase overall score",
    "Skill gaps for this candidate"
]

for query in test_queries:
    print(f"Query: \"{query}\"")
    results = vector_store.search_counterfactuals(query, top_k=3)
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['change']} → +{result.get('overall_impact', 0):.1f} pts "
                  f"(similarity: {result['similarity']:.3f})")
    else:
        print("   No results found")
    print()

print("="*80)
print("✅ COUNTERFACTUAL STORAGE TEST COMPLETE!")
print("="*80 + "\n")

print("📊 Result: Counterfactuals are now queryable via semantic search!")
print("   Use vector_store.search_counterfactuals() to answer 'What if?' questions.\n")
