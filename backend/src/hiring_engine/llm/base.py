"""Abstract LLM client interface."""

from abc import ABC, abstractmethod
from typing import Optional, Type
from pydantic import BaseModel


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate text from a prompt."""
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[BaseModel],
        system: Optional[str] = None,
        temperature: float = 0.3,
    ) -> BaseModel:
        """Generate structured output matching a Pydantic schema."""
        ...
