"""
Digital Den — Adaptive AI Behavior
═══════════════════════════════════════════════════════════════════════════

Module that adapts AI behavior based on user's cognitive state.

Principle:
> AI adapts to state, not to request.
> Same request, different state → different response.

Based on: docs/adaptive_ai_behavior.md, docs/golden_standard_denis.md
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass

from analytics.kaizen_models import UserState
from core.logging import get_logger


logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Behavior Modes
# ═══════════════════════════════════════════════════════════════════════════

class AIBehaviorMode(str, Enum):
    """AI behavior modes based on user state."""
    STRATEGIST = "strategist"   # 🧠 Партнёр-стратег (при росте)
    ANALYST = "analyst"         # 🔍 Логический аналитик (при плато)
    COACH = "coach"             # ❓ Коуч/сократический (при флуктуациях)
    FIXER = "fixer"             # 🧾 Фиксатор (при перегрузе)
    EXPLORER = "explorer"       # 🧪 Исследователь гипотез (при устойчивом росте)


class ThinkingDepth(str, Enum):
    """Thinking depth levels."""
    SHALLOW = "shallow"         # Минимализм, фокус на одном
    STRUCTURED = "structured"   # Базовый режим, стандартный анализ
    DEEP = "deep"               # Глубокий анализ, архитектура, связи


class ResponseLength(str, Enum):
    """Response length preferences."""
    BRIEF = "brief"             # Кратко и чётко
    MEDIUM = "medium"           # Стандартно
    DETAILED = "detailed"       # Развёрнуто, с моделями


# ═══════════════════════════════════════════════════════════════════════════
# Behavior Configuration
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class BehaviorConfig:
    """Complete AI behavior configuration."""
    mode: AIBehaviorMode
    thinking_depth: ThinkingDepth
    response_length: ResponseLength
    focus: str
    forbidden_phrases: list
    allowed_phrases: list
    prompt_additions: str


# ═══════════════════════════════════════════════════════════════════════════
# Adaptive Behavior Service
# ═══════════════════════════════════════════════════════════════════════════

class AdaptiveAIBehavior:
    """
    Adapts AI behavior based on user's cognitive state.
    
    Priority: User State > Request > Manual Settings
    """
    
    # State to behavior mode mapping
    STATE_TO_MODE = {
        UserState.GROWTH: AIBehaviorMode.STRATEGIST,
        UserState.PLATEAU: AIBehaviorMode.ANALYST,
        UserState.FLUCTUATION: AIBehaviorMode.COACH,
        UserState.OVERLOAD: AIBehaviorMode.FIXER,
    }
    
    # Behavior configurations
    BEHAVIOR_CONFIGS = {
        AIBehaviorMode.STRATEGIST: BehaviorConfig(
            mode=AIBehaviorMode.STRATEGIST,
            thinking_depth=ThinkingDepth.DEEP,
            response_length=ResponseLength.DETAILED,
            focus="архитектура, связи, последствия, расширение горизонтов",
            forbidden_phrases=["нужно", "должен", "проблема", "плохо"],
            allowed_phrases=["наблюдается", "возможно", "один из вариантов", "можно рассмотреть"],
            prompt_additions="""
🧠 РЕЖИМ: Партнёр-стратег

Пользователь находится в состоянии РОСТА:
- Положительная динамика
- Высокая связность мышления
- Устойчивые решения

Твои действия:
✅ Усиливай мышление пользователя
✅ Предлагай модели и фреймворки
✅ Расширяй горизонты, показывай связи
✅ Можно быть детальным и глубоким

Запрещено: давать оценки, использовать язык "нужно/должен"
"""
        ),
        
        AIBehaviorMode.ANALYST: BehaviorConfig(
            mode=AIBehaviorMode.ANALYST,
            thinking_depth=ThinkingDepth.STRUCTURED,
            response_length=ResponseLength.MEDIUM,
            focus="причинно-следственные связи, декомпозиция, уточнение",
            forbidden_phrases=["нужно", "должен", "правильный ответ"],
            allowed_phrases=["возможно", "наблюдается", "если рассмотреть"],
            prompt_additions="""
🔍 РЕЖИМ: Логический аналитик

Пользователь находится в состоянии ПЛАТО:
- Стабильность без роста
- Повторяемость формулировок

Твои действия:
✅ Задавай уточняющие вопросы
✅ Предлагай альтернативные углы зрения
✅ Фокус на причинно-следственных связях
✅ Помоги декомпозировать задачи

Не ускоряй. Не подталкивай.
"""
        ),
        
        AIBehaviorMode.COACH: BehaviorConfig(
            mode=AIBehaviorMode.COACH,
            thinking_depth=ThinkingDepth.STRUCTURED,
            response_length=ResponseLength.MEDIUM,
            focus="вопросы важнее ответов, прояснение намерений",
            forbidden_phrases=["нужно", "должен", "сделай", "реши"],
            allowed_phrases=["что для тебя важнее", "как ты видишь", "чего хочешь достичь"],
            prompt_additions="""
❓ РЕЖИМ: Коуч (сократический метод)

Пользователь находится в состоянии ФЛУКТУАЦИЙ:
- Скачки активности
- Частая смена тем
- Возможные противоречия

Твои действия:
✅ Замедляй, не ускоряй
✅ Отражай то, что слышишь
✅ Вопросы важнее ответов
✅ Помогай прояснить намерения
✅ Фиксируй, не советуй

Сократический подход: помоги пользователю самому прийти к пониманию.
"""
        ),
        
        AIBehaviorMode.FIXER: BehaviorConfig(
            mode=AIBehaviorMode.FIXER,
            thinking_depth=ThinkingDepth.SHALLOW,
            response_length=ResponseLength.BRIEF,
            focus="кратко, чётко, зафиксировать и остановиться",
            forbidden_phrases=["можно также", "рассмотрим ещё", "другой вариант"],
            allowed_phrases=["понял", "зафиксировано", "сделано", "следующий шаг"],
            prompt_additions="""
🧾 РЕЖИМ: Фиксатор

Пользователь находится в состоянии ПЕРЕГРУЗА:
- Высокая активность + падение ясности
- Упрощённые формулировки

Твои действия:
✅ МИНИМАЛИЗМ. Кратко!
✅ Фокус на одном
✅ Откажись от сложных моделей
✅ Зафиксируй и остановись
✅ Не добавляй новых идей

Если ответ длиннее 3 предложений — сократи его.
"""
        ),
        
        AIBehaviorMode.EXPLORER: BehaviorConfig(
            mode=AIBehaviorMode.EXPLORER,
            thinking_depth=ThinkingDepth.DEEP,
            response_length=ResponseLength.DETAILED,
            focus="варианты, сценарии, эксперименты, новые подходы",
            forbidden_phrases=["нужно", "единственный путь"],
            allowed_phrases=["что если", "эксперимент", "гипотеза", "вариант"],
            prompt_additions="""
🧪 РЕЖИМ: Исследователь гипотез

Пользователь находится в состоянии УСТОЙЧИВОГО РОСТА:
- Стабильная положительная динамика
- Готовность к новому

Твои действия:
✅ Предлагай варианты и сценарии
✅ Генерируй гипотезы
✅ Предлагай эксперименты
✅ Расширяй пространство возможностей

Креативность приветствуется!
"""
        ),
    }
    
    def __init__(self):
        self.current_mode: Optional[AIBehaviorMode] = None
        self.current_state: Optional[UserState] = None
    
    def select_behavior_mode(
        self,
        user_state: UserState,
        contours: Optional[Dict[str, Any]] = None
    ) -> AIBehaviorMode:
        """
        Select AI behavior mode based on user state.
        
        Can switch to EXPLORER if growth is sustained.
        """
        # Check for sustained growth → Explorer mode
        if user_state == UserState.GROWTH and contours:
            # If all contours are trending up, use Explorer
            up_trends = sum(
                1 for c in contours.values()
                if isinstance(c, dict) and c.get("trend") == "up"
            )
            if up_trends >= 3:
                return AIBehaviorMode.EXPLORER
        
        return self.STATE_TO_MODE.get(user_state, AIBehaviorMode.ANALYST)
    
    def get_behavior_config(
        self,
        mode: AIBehaviorMode
    ) -> BehaviorConfig:
        """Get full behavior configuration for mode."""
        return self.BEHAVIOR_CONFIGS.get(mode, self.BEHAVIOR_CONFIGS[AIBehaviorMode.ANALYST])
    
    def adapt_system_prompt(
        self,
        base_prompt: str,
        user_state: UserState,
        contours: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Adapt system prompt based on user's cognitive state.
        
        This is the main integration point with the orchestrator.
        """
        # Select mode
        mode = self.select_behavior_mode(user_state, contours)
        config = self.get_behavior_config(mode)
        
        # Store current state
        self.current_mode = mode
        self.current_state = user_state
        
        # Add behavior instructions to prompt
        adapted_prompt = base_prompt + config.prompt_additions
        
        logger.info(
            "adaptive_behavior_applied",
            user_state=user_state.value,
            mode=mode.value,
            thinking_depth=config.thinking_depth.value,
        )
        
        return adapted_prompt
    
    def get_response_guidelines(
        self,
        mode: Optional[AIBehaviorMode] = None
    ) -> Dict[str, Any]:
        """
        Get response guidelines for current or specified mode.
        
        Used by agents to adapt their output.
        """
        mode = mode or self.current_mode or AIBehaviorMode.ANALYST
        config = self.get_behavior_config(mode)
        
        return {
            "mode": mode.value,
            "thinking_depth": config.thinking_depth.value,
            "response_length": config.response_length.value,
            "focus": config.focus,
            "forbidden_phrases": config.forbidden_phrases,
            "allowed_phrases": config.allowed_phrases,
            "max_sentences": self._get_max_sentences(config.response_length),
        }
    
    def _get_max_sentences(self, length: ResponseLength) -> int:
        """Get recommended max sentences based on response length."""
        return {
            ResponseLength.BRIEF: 5,
            ResponseLength.MEDIUM: 12,
            ResponseLength.DETAILED: 25,
        }.get(length, 12)
    
    def should_ask_clarifying_question(
        self,
        mode: Optional[AIBehaviorMode] = None
    ) -> bool:
        """Check if current mode encourages clarifying questions."""
        mode = mode or self.current_mode
        return mode in [AIBehaviorMode.COACH, AIBehaviorMode.ANALYST]
    
    def should_provide_alternatives(
        self,
        mode: Optional[AIBehaviorMode] = None
    ) -> bool:
        """Check if current mode encourages providing alternatives."""
        mode = mode or self.current_mode
        return mode in [AIBehaviorMode.STRATEGIST, AIBehaviorMode.EXPLORER]
    
    def explain_mode_change(
        self,
        from_mode: AIBehaviorMode,
        to_mode: AIBehaviorMode
    ) -> str:
        """
        Explain mode change if user asks.
        
        Note: AI should only explain if user explicitly asks.
        """
        mode_names = {
            AIBehaviorMode.STRATEGIST: "партнёр-стратег",
            AIBehaviorMode.ANALYST: "логический аналитик",
            AIBehaviorMode.COACH: "коуч",
            AIBehaviorMode.FIXER: "фиксатор",
            AIBehaviorMode.EXPLORER: "исследователь гипотез",
        }
        
        return (
            f"Я переключился из режима «{mode_names[from_mode]}» "
            f"в режим «{mode_names[to_mode]}», "
            f"потому что заметил изменение в твоём состоянии."
        )


# ═══════════════════════════════════════════════════════════════════════════
# Global Instance
# ═══════════════════════════════════════════════════════════════════════════

adaptive_behavior = AdaptiveAIBehavior()
