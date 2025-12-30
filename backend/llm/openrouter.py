"""
Digital Denis — OpenRouter LLM Provider
═══════════════════════════════════════════════════════════════════════════

OpenRouter API integration for LLM calls.
"""

from typing import Optional, List

import httpx

from core.config import settings
from llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class OpenRouterProvider(BaseLLMProvider):
    """
    OpenRouter LLM provider.
    
    Supports models:
    - anthropic/claude-3.5-sonnet (default)
    - anthropic/claude-3-opus
    - openai/gpt-4-turbo
    - meta-llama/llama-3.1-70b-instruct
    """
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.default_model = settings.default_model
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://digital-denis.app",
            "X-Title": "Digital Denis",
            "Content-Type": "application/json",
        }
    
    async def complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Generate completion from messages."""
        
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
        
        choice = data["choices"][0]
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", model),
            tokens_used=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
        )
    
    async def complete_simple(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """Simple completion with just prompt."""
        
        messages = []
        if system:
            messages.append(LLMMessage(role="system", content=system))
        messages.append(LLMMessage(role="user", content=prompt))
        
        response = await self.complete(messages, model=model)
        return response.content

    async def get_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """Generate embedding for text using /embeddings endpoint."""
        model = model or "openai/text-embedding-ada-002"
        
        payload = {
            "model": model,
            "input": text,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers=self.headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            
        return data["data"][0]["embedding"]

    async def get_embeddings(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """Generate multiple embeddings in one request."""
        model = model or "openai/text-embedding-ada-002"
        
        payload = {
            "model": model,
            "input": texts,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers=self.headers,
                json=payload,
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
            
        # Sort results by index to match input order (OpenRouter usually preserves order)
        # but the API contract for OpenAI-compatible usually implies it.
        results = [None] * len(texts)
        for item in data["data"]:
            results[item["index"]] = item["embedding"]
            
        return results


# Global instance
openrouter = OpenRouterProvider()
