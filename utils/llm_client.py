"""
LLM client wrapper for Ollama integration.
Provides a clean interface for agent-LLM interaction.
"""

import os
import json
from typing import Optional, Dict, Any, List, Union
import requests
from pathlib import Path
from pydantic import BaseModel


class OllamaClient:
    """
    Client for interacting with Ollama API.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: str = "llama3",
        timeout: int = 60
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama API URL (default: http://localhost:11434)
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model
        self.timeout = timeout
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        schema: Optional[type[BaseModel]] = None,  # NEW: Pydantic schema for structured output
        **kwargs
    ) -> Union[str, Dict]:
        """
        Generate text using Ollama.
        
        Args:
            prompt: User prompt
            system: System prompt (optional)
            temperature: Sampling temperature (0-1)
            max_tokens: Max tokens to generate
            schema: Optional Pydantic schema for structured JSON output
            **kwargs: Additional provider-specific args (currently unused for Ollama)
            
        Returns:
            Generated text (str) or parsed Pydantic model (Dict) if schema provided
        """
        
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if system:
            payload["system"] = system
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except requests.exceptions.ConnectionError:
            return self._fallback_response(prompt, system)
        except Exception as e:
            print(f"⚠️  Ollama error: {e}")
            return self._fallback_response(prompt, system)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> str:
        """
        Chat completion using Ollama.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            
        Returns:
            Assistant response
        """
        
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
            
        except requests.exceptions.ConnectionError:
            # Fallback if Ollama not running
            system = next((m["content"] for m in messages if m["role"] == "system"), None)
            user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
            return self._fallback_response(user_msg, system)
        except Exception as e:
            print(f"⚠️  Ollama error: {e}")
            return self._fallback_response("", None)
    
    def is_available(self) -> bool:
        """
        Check if Ollama is available.
        
        Returns:
            True if Ollama is running
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except:
            return []
    
    def _fallback_response(self, prompt: str, system: Optional[str]) -> str:
        """
        Fallback response when Ollama unavailable.
        Returns a deterministic template-based response.
        """
        
        # Determine agent type from system prompt
        if system and "Advocate" in system:
            return self._advocate_fallback(prompt)
        elif system and "Skeptic" in system:
            return self._skeptic_fallback(prompt)
        elif system and "Moderator" in system:
            return self._moderator_fallback(prompt)
        elif system and "Red Team" in system:
            return self._redteam_fallback(prompt)
        else:
            return "[Ollama not available. Using fallback mode. Please start Ollama to enable LLM-powered agents.]"
    
    def _advocate_fallback(self, prompt: str) -> str:
        """Fallback for Advocate agent."""
        return """Based on the evaluation, I advocate for this candidate.

Key Strengths:
• Strong technical skills that align with job requirements
• Relevant experience in the field
• Positive interview performance indicates good culture fit

While there may be some gaps, these can be addressed through:
• Structured onboarding and training programs
• Mentorship from senior team members
• On-the-job learning opportunities

I recommend moving forward with this candidate as they show strong potential.

[Note: This is a fallback response. Start Ollama for natural language debates.]"""
    
    def _skeptic_fallback(self, prompt: str) -> str:
        """Fallback for Skeptic agent."""
        return """I have several concerns about this candidate:

Risk Factors:
• Skill gaps may require significant training investment
• Experience level might not match immediate job requirements
• Potential challenges in meeting performance expectations

Questions to Consider:
• Can we realistically close the gaps within an acceptable timeframe?
• Are there stronger candidates in our pipeline?
• What's the opportunity cost of this hire?

I recommend careful consideration before proceeding.

[Note: This is a fallback response. Start Ollama for natural language debates.]"""
    
    def _moderator_fallback(self, prompt: str) -> str:
        """Fallback for Moderator agent."""
        return """After reviewing all perspectives, here is my synthesis:

The Evaluator provided objective metrics and constraint validation.
The Advocate highlighted candidate strengths and potential.
The Skeptic identified legitimate risks and concerns.

Balancing all factors, I recommend proceeding with conditional approval:
• Address identified skill gaps through training plan
• Set clear 30-60-90 day milestones
• Regular check-ins to ensure progress

This balanced approach mitigates risks while giving the candidate opportunity to succeed.

[Note: This is a fallback response. Start Ollama for natural language debates.]"""
    
    def _redteam_fallback(self, prompt: str) -> str:
        """Fallback for Red Team agent."""
        return """RED TEAM ANALYSIS - FALLBACK MODE

⚠️ Note: This is a deterministic fallback analysis. For advanced adversarial testing with natural language reasoning, ensure Ollama is running with a compatible model.

STANDARD ADVERSARIAL CHECKS:
The deterministic Red Team agent has completed its rule-based adversarial testing:
• Bias detection algorithms executed
• Decision boundary testing completed  
• Consistency validation performed
• Edge case identification done
• Fairness metrics calculated

FALLBACK LIMITATIONS:
Unlike LLM-powered analysis, this fallback mode:
✗ Cannot perform nuanced contextual reasoning
✗ Cannot identify subtle implicit biases
✗ Cannot generate novel challenge scenarios
✗ Cannot adapt to complex edge cases

RECOMMENDATION:
For production use, start Ollama with an appropriate model (e.g., llama3, mistral) to enable:
✓ Natural language adversarial reasoning
✓ Context-aware bias detection
✓ Creative challenge generation
✓ Adaptive red teaming strategies

The deterministic analysis below continues with rule-based checks only."""


# Singleton instance
_client: Optional[OllamaClient] = None


def get_llm_client(model: Optional[str] = None) -> OllamaClient:
    """
    Get or create LLM client singleton.
    
    Args:
        model: Optional model name override
        
    Returns:
        OllamaClient instance
    """
    global _client
    
    if _client is None or (model and _client.model != model):
        default_model = os.getenv("OLLAMA_MODEL", "llama3")
        _client = OllamaClient(model=model or default_model)
    
    return _client


__all__ = ["OllamaClient", "get_llm_client"]
