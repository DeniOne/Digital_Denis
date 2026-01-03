"""
Digital Den — LLM Base Provider
═══════════════════════════════════════════════════════════════════════════

Abstract base class for LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class LLMMessage:
    """Message for LLM conversation."""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    tokens_used: int
    finish_reason: str


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Generate completion from messages."""
        pass
    
    @abstractmethod
    async def complete_simple(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """Simple completion with just prompt."""
        pass
    
    async def classify(
        self,
        text: str,
        categories: List[str],
        model: Optional[str] = None,
    ) -> str:
        """Classify text into one of the categories."""
        categories_str = ", ".join(categories)
        prompt = f"""Classify the following text into one of these categories: {categories_str}

Text: {text}

Return only the category name, nothing else."""
        
        result = await self.complete_simple(prompt, model=model)
        return result.strip()

    @abstractmethod
    async def get_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """Generate embedding for text."""
        pass

    @abstractmethod
    async def get_embeddings(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
