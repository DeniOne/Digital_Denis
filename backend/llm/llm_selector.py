"""
Digital Den — LLM Selector
═══════════════════════════════════════════════════════════════════════════

Unified LLM Selector — автоматический выбор модели по роли задачи.

Роли:
- router: классификация запросов (GPT-4o-mini) — $0.15/M
- fast: рутинные задачи (GPT-4o-mini) — $0.15/M  
- thinking: глубокий reasoning (DeepSeek R1) — $0.55/M
- creative_text: художественный текст (GPT-4o) — $2.50/M
- creative_media: мультимодальный контент (Gemini 3 Flash) — $0.10/M
- default: общие задачи (Claude Sonnet 4.5) — $3/M
- fallback: критические задачи (Claude Opus 4.5) — $10/M
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass

from core.config import settings
from core.logging import get_logger
from llm.base import LLMMessage, LLMResponse

logger = get_logger(__name__)


class ModelRole(str, Enum):
    """Роли моделей в гибридной архитектуре."""
    ROUTER = "router"           # Классификация запросов
    FAST = "fast"               # Рутина, простые задачи
    THINKING = "thinking"       # Глубокий анализ, философия
    CREATIVE_TEXT = "creative_text"  # Книги, истории
    CREATIVE_MEDIA = "creative_media"  # Изображения, мультимодал
    DEFAULT = "default"         # Основные задачи
    FALLBACK = "fallback"       # Критические задачи
    GEMINI_CLI = "gemini_cli"       # Прямой вызов через CLI для глубоких сессий


@dataclass
class ModelConfig:
    """Конфигурация модели."""
    model_id: str
    provider: str  # openrouter, gemini, groq
    cost_per_million: float  # $ per million tokens
    max_tokens: int = 4096
    temperature: float = 0.7


class LLMSelector:
    """
    Центральный селектор LLM — выбирает модель по роли задачи.
    
    Использование:
        response = await llm_selector.complete(
            role=ModelRole.THINKING,
            messages=messages
        )
    """
    
    def __init__(self):
        self._init_model_map()
    
    def _init_model_map(self):
        """Инициализация карты моделей по ролям."""
        self.model_map: Dict[ModelRole, ModelConfig] = {
            ModelRole.ROUTER: ModelConfig(
                model_id=settings.router_model,
                provider="openrouter",
                cost_per_million=0.15,
                max_tokens=1024,
                temperature=0.3,  # Низкая для классификации
            ),
            ModelRole.FAST: ModelConfig(
                model_id=settings.fast_model,
                provider="openrouter",
                cost_per_million=0.15,
                max_tokens=2048,
                temperature=0.7,
            ),
            ModelRole.THINKING: ModelConfig(
                model_id=settings.thinking_model,
                provider="openrouter",
                cost_per_million=0.55,
                max_tokens=8192,
                temperature=0.8,  # Выше для креативного мышления
            ),
            ModelRole.CREATIVE_TEXT: ModelConfig(
                model_id=settings.creative_text_model,
                provider="openrouter",
                cost_per_million=2.50,
                max_tokens=4096,
                temperature=0.9,  # Высокая для творчества
            ),
            ModelRole.CREATIVE_MEDIA: ModelConfig(
                model_id=settings.creative_multimodal_model,
                provider="openrouter",
                cost_per_million=0.10,
                max_tokens=4096,
                temperature=0.7,
            ),
            ModelRole.DEFAULT: ModelConfig(
                model_id=settings.default_model,
                provider="openrouter",
                cost_per_million=3.00,
                max_tokens=4096,
                temperature=0.7,
            ),
            ModelRole.FALLBACK: ModelConfig(
                model_id=settings.thinking_fallback_model, # Claude Opus 4.5
                provider="openrouter",
                cost_per_million=10.0,
                max_tokens=4096,
                temperature=0.7,
            ),
            ModelRole.GEMINI_CLI: ModelConfig(
                model_id="gemini-2.0-flash-exp",
                provider="gemini_cli",
                cost_per_million=0.1, # Символически
                max_tokens=4096,
                temperature=0.7,
            ),
        }
    
    def get_model_config(self, role: ModelRole) -> ModelConfig:
        """Получить конфигурацию модели по роли."""
        return self.model_map.get(role, self.model_map[ModelRole.DEFAULT])
    
    def get_model_id(self, role: ModelRole) -> str:
        """Получить ID модели по роли."""
        return self.get_model_config(role).model_id
    
    async def complete(
        self,
        role: ModelRole,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        fallback_role: Optional[ModelRole] = None,
    ) -> LLMResponse:
        """
        Выполнить запрос к LLM с автоматическим выбором модели.
        
        Args:
            role: Роль модели
            messages: Список сообщений
            temperature: Переопределить температуру
            max_tokens: Переопределить max_tokens
            fallback_role: Роль для fallback при ошибке
        
        Returns:
            LLMResponse с ответом
        """
        from llm.openrouter import openrouter
        from llm.groq import groq
        
        config = self.get_model_config(role)
        
        # Переопределить параметры если указаны
        temp = temperature if temperature is not None else config.temperature
        tokens = max_tokens if max_tokens is not None else config.max_tokens
        
        logger.info(
            "llm_selector_request",
            role=role.value,
            model=config.model_id,
            provider=config.provider,
            cost_per_m=config.cost_per_million,
        )
        
        try:
            # Выбор провайдера — все модели идут через OpenRouter
            if config.provider == "openrouter":
                response = await openrouter.complete(
                    messages=messages,
                    model=config.model_id,
                    temperature=temp,
                    max_tokens=tokens,
                )
            elif config.provider == "gemini":
                # Lazy import для Gemini (только если используется напрямую)
                try:
                    from llm.gemini import gemini
                    response = await gemini.complete(
                        messages=messages,
                        model=config.model_id,
                        temperature=temp,
                        max_tokens=tokens,
                    )
                except ImportError:
                    # Fallback to OpenRouter if Gemini not available
                    logger.warning("gemini_import_failed, using openrouter")
                    response = await openrouter.complete(
                        messages=messages,
                        model=config.model_id,
                        temperature=temp,
                        max_tokens=tokens,
                    )
            elif config.provider == "gemini_cli":
                from llm.gemini_cli_provider import gemini_cli
                response = await gemini_cli.complete(
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens,
                    model=config.model_id
                )
            elif config.provider == "groq":
                response = await groq.complete(
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens,
                )
            else:
                # Fallback to OpenRouter
                response = await openrouter.complete(
                    messages=messages,
                    model=config.model_id,
                    temperature=temp,
                    max_tokens=tokens,
                )
            
            logger.info(
                "llm_selector_success",
                role=role.value,
                model=response.model,
                tokens=response.tokens_used,
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "llm_selector_error",
                role=role.value,
                model=config.model_id,
                error=str(e),
            )
            
            # Попробовать fallback
            if fallback_role and fallback_role != role:
                logger.warning(
                    "llm_selector_fallback",
                    from_role=role.value,
                    to_role=fallback_role.value,
                )
                return await self.complete(
                    role=fallback_role,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    fallback_role=None,  # Не зацикливаемся
                )
            
            raise
    
    async def complete_simple(
        self,
        role: ModelRole,
        prompt: str,
        system: Optional[str] = None,
        fallback_role: Optional[ModelRole] = None,
    ) -> str:
        """Простой запрос с prompt и system."""
        messages = []
        if system:
            messages.append(LLMMessage(role="system", content=system))
        messages.append(LLMMessage(role="user", content=prompt))
        
        response = await self.complete(
            role=role,
            messages=messages,
            fallback_role=fallback_role,
        )
        return response.content


# Global instance
llm_selector = LLMSelector()
