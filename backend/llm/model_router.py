"""
Digital Den — Model Router
═══════════════════════════════════════════════════════════════════════════

Классификатор запросов для автоматического выбора модели.

Использует GPT-4o-mini ($0.15/M) для быстрой классификации типа задачи,
затем направляет на соответствующую модель.

Категории:
- routine: простые вопросы, команды → GPT-4o-mini
- thinking: философия, самоанализ, сложная логика → DeepSeek R1  
- creative: книги, истории, стихи → GPT-4o
- analysis: данные, статистика → Claude Sonnet
"""

import json
import re
from typing import Optional
from enum import Enum

from core.config import settings
from core.logging import get_logger
from llm.llm_selector import llm_selector, ModelRole

logger = get_logger(__name__)


class TaskCategory(str, Enum):
    """Категории задач для маршрутизации."""
    ROUTINE = "routine"         # Простые вопросы, команды, small talk
    THINKING = "thinking"       # Философия, самоанализ, глубокий reasoning
    CREATIVE = "creative"       # Книги, истории, стихи, творчество
    ANALYSIS = "analysis"       # Данные, статистика, аналитика
    SCHEDULE = "schedule"       # Расписание, напоминания (специальный агент)


# Маппинг категорий на роли моделей
CATEGORY_TO_ROLE = {
    TaskCategory.ROUTINE: ModelRole.FAST,
    TaskCategory.THINKING: ModelRole.THINKING,
    TaskCategory.CREATIVE: ModelRole.CREATIVE_TEXT,
    TaskCategory.ANALYSIS: ModelRole.DEFAULT,
    TaskCategory.SCHEDULE: ModelRole.FAST,  # Schedule agent использует быструю модель
}


class ModelRouter:
    """
    Маршрутизатор моделей — классифицирует запрос и выбирает оптимальную модель.
    
    Принцип работы:
    1. Быстрая проверка по ключевым словам (бесплатно)
    2. При неуверенности — классификация через GPT-4o-mini (дёшево)
    3. Возврат категории и рекомендуемой роли модели
    """
    
    # Ключевые слова для быстрой классификации (без LLM)
    ROUTINE_KEYWORDS = [
        "привет", "пока", "спасибо", "хорошо", "ок", "понял",
        "который час", "какой день", "погода",
        "да", "нет", "ладно", "окей",
    ]
    
    THINKING_KEYWORDS = [
        "философ", "смысл жизни", "почему я", "кто я", "зачем",
        "проанализируй", "подумай", "размышлени", "глубоко",
        "kaizen", "кайдзен", "самоанализ", "рефлексия",
        "цель жизни", "предназначен", "миссия",
    ]
    
    CREATIVE_KEYWORDS = [
        "напиши рассказ", "придумай историю", "сочини", "стих",
        "глава книги", "продолжи историю", "начало романа",
        "сценарий", "диалог персонаж", "художественн",
    ]
    
    SCHEDULE_KEYWORDS = [
        "напомни", "напоминание", "встреча", "расписание", 
        "задача", "дедлайн", "запланируй", "таблетки", "лекарств",
    ]
    
    ANALYSIS_KEYWORDS = [
        "статистик", "данные", "график", "тренд", "метрик",
        "анализ данных", "отчёт", "сравни", "процент",
    ]
    
    async def classify(self, message: str) -> tuple[TaskCategory, ModelRole, float]:
        """
        Классифицировать запрос и определить оптимальную модель.
        
        Returns:
            (category, model_role, confidence)
        """
        message_lower = message.lower()
        
        # 1. Быстрая проверка по ключевым словам
        quick_result = self._quick_classify(message_lower)
        if quick_result and quick_result[2] > 0.8:  # Высокая уверенность
            logger.info(
                "model_router_quick",
                category=quick_result[0].value,
                confidence=quick_result[2],
            )
            return quick_result
        
        # 2. LLM классификация для неоднозначных случаев
        try:
            llm_result = await self._llm_classify(message)
            logger.info(
                "model_router_llm",
                category=llm_result[0].value,
                confidence=llm_result[2],
            )
            return llm_result
        except Exception as e:
            logger.warning("model_router_llm_error", error=str(e))
            # Fallback на quick result или default
            if quick_result:
                return quick_result
            return (TaskCategory.ROUTINE, ModelRole.DEFAULT, 0.5)
    
    def _quick_classify(self, message_lower: str) -> Optional[tuple[TaskCategory, ModelRole, float]]:
        """Быстрая классификация по ключевым словам."""
        
        # Проверяем в порядке приоритета
        if any(kw in message_lower for kw in self.SCHEDULE_KEYWORDS):
            return (TaskCategory.SCHEDULE, ModelRole.FAST, 0.9)
        
        if any(kw in message_lower for kw in self.THINKING_KEYWORDS):
            return (TaskCategory.THINKING, ModelRole.THINKING, 0.85)
        
        if any(kw in message_lower for kw in self.CREATIVE_KEYWORDS):
            return (TaskCategory.CREATIVE, ModelRole.CREATIVE_TEXT, 0.85)
        
        if any(kw in message_lower for kw in self.ANALYSIS_KEYWORDS):
            return (TaskCategory.ANALYSIS, ModelRole.DEFAULT, 0.8)
        
        if any(kw in message_lower for kw in self.ROUTINE_KEYWORDS):
            return (TaskCategory.ROUTINE, ModelRole.FAST, 0.9)
        
        # Короткие сообщения обычно рутина
        if len(message_lower) < 30:
            return (TaskCategory.ROUTINE, ModelRole.FAST, 0.7)
        
        return None
    
    async def _llm_classify(self, message: str) -> tuple[TaskCategory, ModelRole, float]:
        """Классификация через LLM (GPT-4o-mini)."""
        
        prompt = f"""Классифицируй запрос пользователя в одну из категорий:

Запрос: "{message[:500]}"

Категории:
- routine: простые вопросы, команды, приветствия, small talk
- thinking: философия, глубокий анализ, самоанализ, размышления о жизни
- creative: творческие задачи, написание текстов, историй, стихов
- analysis: анализ данных, статистика, отчёты
- schedule: напоминания, расписание, встречи, задачи

Верни JSON (без markdown!):
{{"category": "routine|thinking|creative|analysis|schedule", "confidence": 0.0-1.0}}

ТОЛЬКО JSON:"""

        try:
            response = await llm_selector.complete_simple(
                role=ModelRole.ROUTER,
                prompt=prompt,
            )
            
            # Парсинг JSON
            content = response.strip()
            if content.startswith("```"):
                content = re.sub(r"```(?:json)?\n?", "", content).strip()
            
            data = json.loads(content)
            category = TaskCategory(data.get("category", "routine"))
            confidence = float(data.get("confidence", 0.7))
            role = CATEGORY_TO_ROLE.get(category, ModelRole.DEFAULT)
            
            return (category, role, confidence)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("model_router_parse_error", error=str(e))
            return (TaskCategory.ROUTINE, ModelRole.DEFAULT, 0.5)
    
    def get_role_for_category(self, category: TaskCategory) -> ModelRole:
        """Получить роль модели для категории."""
        return CATEGORY_TO_ROLE.get(category, ModelRole.DEFAULT)


# Global instance
model_router = ModelRouter()
