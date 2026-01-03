"""
Digital Den — Intent Analyzer
═══════════════════════════════════════════════════════════════════════════

Advanced intent analysis for incoming user requests.
Extracts: category, confidence, emotional_state, urgency, requires_clarification.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

from llm.openrouter import openrouter
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Intent Types
# ═══════════════════════════════════════════════════════════════════════════

class RequestCategory(str, Enum):
    """Categories of user requests."""
    STRATEGIC = "strategic"      # Долгосрочное планирование, видение
    ANALYTICAL = "analytical"    # Анализ данных, метрики
    OPERATIONAL = "operational"  # Задачи, действия
    REFLEXIVE = "reflexive"      # Мета-мышление, самоанализ
    META = "meta"                # О системе самой
    SCHEDULE = "schedule"        # Расписание, напоминания
    CREATIVE = "creative"        # Творческие задачи
    SOCIAL = "social"            # Общение, small talk


class EmotionalState(str, Enum):
    """Detected emotional state of the user."""
    NEUTRAL = "neutral"
    POSITIVE = "positive"       # Радость, энтузиазм
    NEGATIVE = "negative"       # Фрустрация, раздражение
    STRESSED = "stressed"       # Стресс, срочность
    CURIOUS = "curious"         # Любопытство, интерес
    CONFUSED = "confused"       # Непонимание, замешательство


class ActionType(str, Enum):
    """What type of action the user expects."""
    ANSWER = "answer"           # Ответ на вопрос
    EXECUTE = "execute"         # Выполнить действие
    PLAN = "plan"               # Составить план
    REMEMBER = "remember"       # Сохранить в память
    REMIND = "remind"           # Напомнить позже
    ANALYZE = "analyze"         # Проанализировать
    CLARIFY = "clarify"         # Уточнить


# ═══════════════════════════════════════════════════════════════════════════
# Intent Analysis Result
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class IntentAnalysis:
    """Complete analysis of user intent."""
    
    # Primary classification
    category: RequestCategory = RequestCategory.OPERATIONAL
    confidence: float = 0.5  # 0-1, насколько уверен в классификации
    
    # Emotional context
    emotional_state: EmotionalState = EmotionalState.NEUTRAL
    urgency: float = 0.5  # 0-1, насколько срочно
    
    # Action hints
    action_type: ActionType = ActionType.ANSWER
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    
    # Extracted entities
    topics: List[str] = field(default_factory=list)
    time_references: List[str] = field(default_factory=list)
    
    # Raw data
    raw_response: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# Intent Analyzer
# ═══════════════════════════════════════════════════════════════════════════

class IntentAnalyzer:
    """
    Analyzes user messages to extract intent, emotional state, and action hints.
    
    Uses LLM for nuanced understanding of Russian text.
    """
    
    # Keywords for quick classification (fallback)
    SCHEDULE_KEYWORDS = [
        "напомни", "напоминание", "встреча", "расписание", "задача", "дедлайн",
        "поставь", "запланируй", "в расписание", "событие", "таблетки", "лекарств"
    ]
    
    STRATEGIC_KEYWORDS = [
        "стратегия", "планирование", "видение", "долгосрочн", "цель", "миссия"
    ]
    
    ANALYTICAL_KEYWORDS = [
        "анализ", "данные", "метрики", "статистика", "тренд", "график"
    ]
    
    async def analyze(self, message: str) -> IntentAnalysis:
        """
        Analyze user message and extract intent.
        
        Returns IntentAnalysis with all detected signals.
        """
        
        # Strip common prefixes (like voice recognition)
        clean_message = re.sub(r"^(🎤 )?Распознано: ", "", message)
        message_lower = clean_message.lower()
        
        # Quick keyword check for schedule
        if any(kw in message_lower for kw in self.SCHEDULE_KEYWORDS):
            # Lower confidence to allow LLM to override if it's a meta-question
            quick_result = IntentAnalysis(
                category=RequestCategory.SCHEDULE,
                confidence=0.6, 
                action_type=ActionType.REMIND,
            )
            return await self._full_analysis(clean_message, quick_hint=quick_result)
        
        # Full LLM analysis
        return await self._full_analysis(clean_message)
    
    async def _full_analysis(
        self, 
        message: str, 
        quick_hint: Optional[IntentAnalysis] = None
    ) -> IntentAnalysis:
        """Perform full LLM-based analysis."""
        
        prompt = f"""Проанализируй сообщение пользователя и определи его намерение.

Сообщение: "{message[:500]}"

Верни JSON (без markdown!):
{{
    "category": "strategic|analytical|operational|reflexive|meta|schedule|creative|social",
    "confidence": 0.0-1.0,
    "emotional_state": "neutral|positive|negative|stressed|curious|confused",
    "urgency": 0.0-1.0,
    "action_type": "answer|execute|plan|remember|remind|analyze|clarify",
    "requires_clarification": true|false,
    "clarification_question": null,
    "topics": ["тема1", "тема2"],
    "time_references": ["завтра", "в 15:00"]
}}

Правила:
1. category:
   - strategic: долгосрочное планирование, видение
   - analytical: анализ данных, метрики
   - operational: задачи, действия (по умолчанию)
   - reflexive: размышления о себе, самоанализ
   - meta: вопросы о системе ИИ
   - schedule: расписание, напоминания, встречи
   - creative: творческие задачи, генерация
   - social: приветствия, small talk

2. confidence: уверенность в классификации (0.5 — не уверен, 1.0 — точно)

3. emotional_state:
   - positive: радость, энтузиазм, "круто", "отлично"
   - negative: раздражение, "опять", "достало"
   - stressed: срочность, "срочно", "быстрее"
   - curious: вопросы, интерес
   - confused: непонимание, "не понял"

4. urgency: 0.0 — не срочно, 1.0 — очень срочно

5. requires_clarification: если нет важной информации

Верни ТОЛЬКО JSON:"""

        try:
            result = await openrouter.complete_simple(
                prompt,
                model=settings.cheap_model
            )
            
            # Clean response
            content = result.strip()
            if content.startswith("```"):
                content = re.sub(r"```(?:json)?\n?", "", content)
                content = content.strip()
            
            data = json.loads(content)
            
            analysis = IntentAnalysis(
                category=RequestCategory(data.get("category", "operational")),
                confidence=float(data.get("confidence", 0.5)),
                emotional_state=EmotionalState(data.get("emotional_state", "neutral")),
                urgency=float(data.get("urgency", 0.5)),
                action_type=ActionType(data.get("action_type", "answer")),
                requires_clarification=bool(data.get("requires_clarification", False)),
                clarification_question=data.get("clarification_question"),
                topics=data.get("topics", []),
                time_references=data.get("time_references", []),
                raw_response=content,
            )
            
            # Merge with quick hint if provided
            if quick_hint and quick_hint.confidence > analysis.confidence:
                analysis.category = quick_hint.category
                analysis.action_type = quick_hint.action_type
            
            logger.info(
                "intent_analyzed",
                category=analysis.category.value,
                confidence=analysis.confidence,
                emotional_state=analysis.emotional_state.value,
                urgency=analysis.urgency,
            )
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.warning("intent_parse_error", error=str(e))
            return self._fallback_analysis(message)
        except Exception as e:
            logger.error("intent_analysis_error", error=str(e))
            return self._fallback_analysis(message)
    
    def _fallback_analysis(self, message: str) -> IntentAnalysis:
        """Fallback keyword-based analysis when LLM fails."""
        
        message_lower = message.lower()
        
        # Determine category
        category = RequestCategory.OPERATIONAL
        if any(kw in message_lower for kw in self.SCHEDULE_KEYWORDS):
            category = RequestCategory.SCHEDULE
        elif any(kw in message_lower for kw in self.STRATEGIC_KEYWORDS):
            category = RequestCategory.STRATEGIC
        elif any(kw in message_lower for kw in self.ANALYTICAL_KEYWORDS):
            category = RequestCategory.ANALYTICAL
        elif "?" in message:
            category = RequestCategory.OPERATIONAL
        
        # Detect urgency keywords
        urgency = 0.5
        if any(kw in message_lower for kw in ["срочно", "быстро", "сейчас", "немедленно"]):
            urgency = 0.9
        
        # Detect emotional state
        emotional_state = EmotionalState.NEUTRAL
        if any(kw in message_lower for kw in ["спасибо", "отлично", "круто", "супер"]):
            emotional_state = EmotionalState.POSITIVE
        elif any(kw in message_lower for kw in ["срочно", "быстро", "успеть"]):
            emotional_state = EmotionalState.STRESSED
        elif "?" in message:
            emotional_state = EmotionalState.CURIOUS
        
        return IntentAnalysis(
            category=category,
            confidence=0.6,
            emotional_state=emotional_state,
            urgency=urgency,
        )
    
    async def quick_classify(self, message: str) -> str:
        """Quick classification returning just the category string."""
        analysis = await self.analyze(message)
        return analysis.category.value


# Global instance
intent_analyzer = IntentAnalyzer()
