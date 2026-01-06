"""
Digital Den — Gemini LLM Provider
═══════════════════════════════════════════════════════════════════════════

Google Gemini API integration using httpx for manual REST calls.
"""

import json
from typing import Optional, List, Dict, Any

import httpx

from core.config import settings
from llm.base import BaseLLMProvider, LLMMessage, LLMResponse
from core.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini LLM provider.
    
    Supports models:
    - gemini-1.5-pro (default for reasoning)
    - gemini-1.5-flash
    - gemini-2.0-flash-exp
    """
    
    def __init__(self):
        self.api_key = settings.google_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.default_model = settings.reasoning_model
        
    async def complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Generate completion from messages using Gemini API."""
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not configured")
            
        model = model or self.default_model
        
        # Convert messages to Gemini format
        contents = []
        system_instruction = None
        
        for msg in messages:
            if msg.role == "system":
                system_instruction = {"parts": [{"text": msg.content}]}
            else:
                role = "user" if msg.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        
        if system_instruction:
            payload["system_instruction"] = system_instruction
            
        url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                timeout=120.0,
            )
            
            if response.status_code != 200:
                logger.error("gemini_api_error", status=response.status_code, text=response.text)
                response.raise_for_status()
                
            data = response.json()
            
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            # Gemini doesn't always provide detailed token usage in the same way as OpenAI
            # but we try to extract it if available
            usage = data.get("usageMetadata", {})
            tokens_used = usage.get("totalTokenCount", 0)
            finish_reason = data["candidates"][0].get("finishReason", "stop")
            
            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens_used,
                finish_reason=finish_reason.lower(),
            )
        except (KeyError, IndexError) as e:
            logger.error("gemini_parse_error", error=str(e), data=data)
            raise ValueError(f"Failed to parse Gemini response: {str(e)}")

    async def complete_simple(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """Simple completion with prompt and optional system instruction."""
        messages = []
        if system:
            messages.append(LLMMessage(role="system", content=system))
        messages.append(LLMMessage(role="user", content=prompt))
        
        response = await self.complete(messages, model=model)
        return response.content

    async def get_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """Generate embedding using Gemini API."""
        model = model or "text-embedding-004"
        
        url = f"{self.base_url}/{model}:embedContent?key={self.api_key}"
        payload = {
            "model": f"models/{model}",
            "content": {"parts": [{"text": text}]}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            
        return data["embedding"]["values"]

    async def get_embeddings(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """Generate multiple embeddings in one batch request."""
        model = model or "text-embedding-004"
        
        url = f"{self.base_url}/{model}:batchEmbedContents?key={self.api_key}"
        requests = [
            {"model": f"models/{model}", "content": {"parts": [{"text": t}]}}
            for t in texts
        ]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"requests": requests}, timeout=120.0)
            response.raise_for_status()
            data = response.json()
            
        return [item["values"] for item in data["embeddings"]]


# Global instance
gemini = GeminiProvider()
