"""
Digital Den — Gemini CLI Adapter
═══════════════════════════════════════════════════════════════════════════

Adapter for calling Google Gemini CLI via subprocess.
Used for deep reasoning, Kaizen analysis and interactive "CLI" agent sessions.
"""

import asyncio
import subprocess
from typing import List, Optional
from core.config import settings
from core.logging import get_logger
from llm.base import LLMMessage, LLMResponse

logger = get_logger(__name__)

class GeminiCLIProvider:
    """
    Provider that interacts with 'gemini-chat-cli' installed in the system.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash-latest"):
        self.api_key = api_key # Can be None for OAuth
        self.cli_command = "/usr/bin/gemini" 
        
    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: str = "gemini-1.5-flash-latest" 
    ) -> LLMResponse:
        """
        Generate completion using Gemini CLI.
        """
        prompt = self._format_messages(messages)
        
        logger.info("gemini_cli_request", prompt_len=len(prompt))
        
        try:
            # Вызов: /usr/bin/gemini "prompt"
            # Передаем API ключ через переменную окружения для безопасности
            # ВАЖНО: Gemini CLI использует GEMINI_API_KEY, не GOOGLE_API_KEY
            env = {
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "HOME": "/tmp"  # Для хранения кеша CLI
            }
            
            # Если задан API ключ - используем его, иначе (None) - полагаемся на OAuth токены
            if self.api_key:
                env["GEMINI_API_KEY"] = self.api_key
            
            process = await asyncio.create_subprocess_exec(
                self.cli_command,
                "-m",
                model,
                "-p",
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error("gemini_cli_error", code=process.returncode, error=error_msg)
                raise Exception(f"Gemini CLI error: {error_msg}")
            
            content = stdout.decode().strip()
            
            # Remove any CLI artifacts (like "Gemini> " prompts if they exist)
            content = self._clean_output(content)
            
            return LLMResponse(
                content=content,
                model=f"cli:{model}",
                tokens_used=len(content) // 4, # Estimated
            )
            
        except Exception as e:
            logger.error("gemini_cli_exception", error=str(e))
            raise
            
    def _format_messages(self, messages: List[LLMMessage]) -> str:
        """Format history into a single string for CLI."""
        formatted = []
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            if msg.role == "system":
                formatted.append(f"Instructions: {msg.content}")
            else:
                formatted.append(f"{role}: {msg.content}")
        
        return "\n\n".join(formatted) + "\n\nAssistant:"

    def _clean_output(self, text: str) -> str:
        """Clean CLI specific formatting."""
        # Simple for now, can be expanded if the specific CLI adds headers/footers
        return text.strip()

# Global instance
gemini_cli = GeminiCLIProvider(api_key=None)
