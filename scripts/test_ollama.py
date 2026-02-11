"""
Test Ollama connection and model availability.
"""

import requests
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.llm_client import get_llm_client

def test_ollama_connection():
    """Test if Ollama is running and accessible."""
    
    print("=" * 70)
    print("OLLAMA CONNECTION TEST")
    print("=" * 70)
    
    # Test 1: Check if Ollama is running
    print("\n[1] Testing Ollama API endpoint (http://localhost:11434)...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is RUNNING and accessible")
            
            # List available models
            data = response.json()
            models = data.get("models", [])
            if models:
                print(f"\n📦 Available models ({len(models)}):")
                for model in models:
                    print(f"   - {model['name']} (size: {model.get('size', 0) / 1e9:.2f} GB)")
            else:
                print("\n⚠️ Ollama is running but NO MODELS are downloaded!")
                print("   Download a model: ollama pull llama3")
        else:
            print(f"❌ Ollama returned status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama (Connection refused)")
        print("   Ollama is either NOT RUNNING or not on port 11434")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Test using our LLM client
    print("\n[2] Testing LLM Client wrapper...")
    llm = get_llm_client()
    
    if llm.is_available():
        print("✅ LLM Client reports: Ollama is AVAILABLE")
        models = llm.list_models()
        print(f"   Models detected: {', '.join(models) if models else 'None'}")
    else:
        print("❌ LLM Client reports: Ollama is NOT AVAILABLE")
    
    # Test 3: Try actual generation
    print("\n[3] Testing actual text generation...")
    try:
        test_prompt = "Say 'Hello, I am working!' in exactly 5 words."
        response = llm.generate(
            prompt=test_prompt,
            temperature=0.1,
            max_tokens=50
        )
        
        if "[Ollama not available" in response or "FALLBACK MODE" in response:
            print("❌ Generation FAILED - Using fallback mode")
            print(f"   Response: {response[:200]}")
        else:
            print("✅ Generation SUCCESSFUL!")
            print(f"   Response: {response.strip()}")
    except Exception as e:
        print(f"❌ Generation error: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("DIAGNOSIS:")
    print("=" * 70)
    
    llm_available = llm.is_available()
    models = llm.list_models()
    
    if llm_available and models:
        print("✅ STATUS: Ollama is FULLY FUNCTIONAL")
        print(f"   Your project IS using Ollama (Model: {llm.model})")
        print("   The drive location (C: vs D:) doesn't matter for Ollama.")
    elif llm_available and not models:
        print("⚠️ STATUS: Ollama is running but NO MODELS downloaded")
        print("   SOLUTION: Run 'ollama pull llama3' or 'ollama pull mistral'")
    else:
        print("❌ STATUS: Ollama is NOT RUNNING")
        print("   SOLUTION:")
        print("   1. Start Ollama (check system tray or run 'ollama serve')")
        print("   2. Verify it's on port 11434")
        print("   3. Your project will automatically connect once it's running")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_ollama_connection()
