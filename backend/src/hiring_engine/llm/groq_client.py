"""Groq API client — free tier with Llama 3.3 70B."""

import json
import logging
from typing import Optional, Type

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from hiring_engine.llm.base import BaseLLMClient
from hiring_engine.config import get_settings

logger = logging.getLogger(__name__)


class GroqLLMClient(BaseLLMClient):
    """LLM client using Groq API (free tier, Llama 3.3 70B)."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        from groq import AsyncGroq

        settings = get_settings()
        self._api_key = api_key or settings.groq_api_key
        self._model_name = model or settings.groq_model
        self._client = AsyncGroq(api_key=self._api_key)

        logger.info("Groq client initialized: model=%s", self._model_name)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(
            "Groq API retry %d: %s", retry_state.attempt_number, retry_state.outcome.exception()
        ),
    )
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate text from Groq."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or 2048,
        )

        text = response.choices[0].message.content or ""
        logger.debug("Groq response: %d chars", len(text))
        return text

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
    )
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[BaseModel],
        system: Optional[str] = None,
        temperature: float = 0.3,
    ) -> BaseModel:
        """Generate structured output matching a Pydantic schema."""
        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)

        structured_prompt = f"""{prompt}

You MUST respond with ONLY valid JSON matching this schema:
{schema_json}

Return ONLY the JSON object, no markdown, no explanation."""

        text = await self.generate(prompt=structured_prompt, system=system, temperature=temperature)
        text = text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()
            if text.startswith("json"):
                text = text[4:].strip()

        data = json.loads(text)
        return response_schema.model_validate(data)


__all__ = ["GroqLLMClient"]
