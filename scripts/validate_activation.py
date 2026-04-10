"""
Quick validation script - Verify activated features work correctly.

Tests:
1. RAG vector search loading
2. Counterfactual indexing  
3. LLM schema validation
4. Hybrid retrieval initialization
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

print("\n" + "="*80)
print("ACTIVATED FEATURES VALIDATION")
print("="*80 + "\n")

passed = 0
failed = 0

# Test 1: RAG Vector Store
print("1️⃣  Testing RAG Vector Store...")
try:
    from rag.vector_store import VectorStore
    vs = VectorStore()
    # Check methods exist
    assert hasattr(vs, 'index_counterfactuals'), "Missing index_counterfactuals"
    assert hasattr(vs, 'search_counterfactuals'), "Missing search_counterfactuals"
    print("   ✅ VectorStore loaded with counterfactual methods")
    passed += 1
except Exception as e:
    print(f"   ❌ Failed: {e}")
    failed += 1

# Test 2: LLM Schemas
print("\n2️⃣  Testing LLM Schemas...")
try:
    from utils.llm_schemas import (
        AdvocateResponse,
        SkepticResponse,
        ModeratorResponse,
        CounterfactualResponse
    )
    # Validate schema structure
    test_data = {
        "strengths": ["Python expert"],
        "growth_opportunities": [],
        "hire_recommendation": True,
        "confidence": 0.85,
        "key_argument": "Strong technical skills"
    }
    response = AdvocateResponse(**test_data)
    assert response.confidence == 0.85
    print("   ✅ Pydantic schemas validated")
    passed += 1
except Exception as e:
    print(f"   ❌ Failed: {e}")
    failed += 1

# Test 3: Hybrid Retrieval
print("\n3️⃣  Testing Hybrid Retrieval Option...")
try:
    from tools.memory_query import MemoryQueryHelper
    
    # Standard (vector only)
    memory_std = MemoryQueryHelper(use_hybrid=False)
    assert memory_std.use_hybrid == False
    
    # Hybrid (may fail if graph not built, that's OK)
    memory_hybrid = MemoryQueryHelper(use_hybrid=True)
    print("   ✅ Hybrid retrieval option available")
    passed += 1
except Exception as e:
    print(f"   ❌ Failed: {e}")
    failed += 1

# Test 4: Scoring Module
print("\n4️⃣  Testing Scoring Module...")
try:
    from tools import scoring
    from data.schemas import CandidateProfile, JobRequirements
    
    # Create minimal test objects
    candidate = CandidateProfile(
        candidate_id="test_001",
        name="Test Candidate",
        skills=["Python"],
        experience_years=5,
        education="Bachelor"
    )
    
    job = JobRequirements(
        job_id="job_001",
        title="Software Engineer",
        required_skills=["Python"],
        min_experience_years=3,
        required_education="Bachelor"
    )
    
    # This should not crash
    result = scoring.calculate_skill_match(
        candidate.skills,
        job.required_skills,
        []
    )
    assert 'overall_score' in result
    print("   ✅ Scoring module works")
    passed += 1
except Exception as e:
    print(f"   ❌ Failed: {e}")
    failed += 1

print("\n" + "="*80)
print(f"VALIDATION COMPLETE: {passed} passed, {failed} failed")
print("="*80 + "\n")

if failed == 0:
    print("🎉 All activated features validated successfully!\n")
    sys.exit(0)
else:
    print(f"⚠️  {failed} test(s) failed - review errors above\n")
    sys.exit(1)
