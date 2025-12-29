"""
Digital Denis — Groq LLM Provider
═══════════════════════════════════════════════════════════════════════════

Groq API integration for fast/cheap LLM calls and voice transcription.
"""

from typing import Optional, List
from pathlib import Path

import httpx

from core.config import settings
from llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class GroqProvider(BaseLLMProvider):
    """
    Groq LLM provider for fast inference.
    
    Used for:
    - Cheap tasks (classification, topic extraction)
    - Voice transcription (Whisper)
    """
    
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.base_url = settings.groq_base_url
        self.default_model = settings.groq_model
        self.whisper_model = settings.groq_whisper_model
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
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
                timeout=60.0,
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
    
    async def transcribe_audio(
        self,
        audio_path: Path,
        language: str = "ru",
    ) -> str:
        """Transcribe audio file using Whisper."""
        
        async with httpx.AsyncClient() as client:
            with open(audio_path, "rb") as f:
                files = {
                    "file": (audio_path.name, f, "audio/ogg"),
                    "model": (None, self.whisper_model),
                    "language": (None, language),
                }
                
                response = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files,
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
        
        return data.get("text", "")


# Global instance
groq = GroqProvider()
