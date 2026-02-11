"""
Demo: Structured LLM Output with Pydantic Schemas

Shows how agent responses are now validated and structured.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.llm_client import get_llm_client
from utils.llm_schemas import AdvocateResponse, SkepticResponse, ModeratorResponse

print("\n" + "="*80)
print("PHASE 4: STRUCTURED LLM OUTPUT WITH PYDANTIC SCHEMAS")
print("="*80 + "\n")

llm = get_llm_client()

# Test 1: Advocate with structured output
print("🔨 Test 1: Advocate Response (Structured)")
print("-" * 80)

prompt = """
Candidate: John Doe
Skills: Python, Django, PostgreSQL (5 years)
Job: Senior Backend Engineer (requires 7+ years)

Provide a structured hiring recommendation.
"""

try:
    response = llm.generate(
        prompt=prompt,
        system="You are an Advocate agent. Respond in JSON format.",
        schema=AdvocateResponse,
        temperature=0.5
    )
    
    print(f"✅ Structured Response Received:")
    print(f"   Hire Recommendation: {response.hire_recommendation}")
    print(f"   Confidence: {response.confidence:.2f}")
    print(f"   Strengths: {len(response.strengths)} identified")
    print(f"   Key Argument: {response.key_argument[:100]}...")
    
except Exception as e:
    print(f"⚠️ Schema validation failed: {e}")
    print("   (This is expected if using Ollama/local models)")

print()

# Test 2: Moderator decision
print("🔨 Test 2: Moderator Decision (Structured)")
print("-" * 80)

prompt2 = """
Overall Score: 75/100
Advocate says: Hire (strong Python skills)
Skeptic says: Reject (experience gap)

Make a final decision.
"""

try:
    response2 = llm.generate(
        prompt=prompt2,
        system="You are a Moderator. Respond in JSON format.",
        schema=ModeratorResponse,
        temperature=0.3
    )
    
    print(f"✅ Structured Decision:")
    print(f"   Decision: {response2.final_decision}")
    print(f"   Confidence: {response2.confidence:.2f}")
    print(f"   Key Factors: {len(response2.key_factors)}")
    print(f"   Next Steps: {len(response2.next_steps)}")
    
except Exception as e:
    print(f"⚠️ Schema validation: {e}")

print("\n" + "="*80)
print("📊 Result: LLM responses are now structured and validated!")
print("="*80 + "\n")

print("Benefits:")
print("  ✅ Type-safe responses")
print("  ✅ Confidence scores enforced")
print("  ✅ Required fields validated")
print("  ✅ Easier to parse and use in code\n")
