"""
Digital Denis — User Settings Service
═══════════════════════════════════════════════════════════════════════════

Service for loading and applying user settings.
"""

from typing import Optional, List
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import UserSettings
from analytics.cal_models import Rule
from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class UserSettingsContext:
    """User settings context for AI behavior."""
    
    # Behavior
    ai_role: str = "partner_strategic"
    thinking_depth: str = "structured"
    response_style: str = "detailed"
    confrontation_level: str = "argumented"
    
    # Autonomy
    initiative_level: str = "suggest"
    intervention_frequency: str = "realtime"
    allowed_actions: List[str] = None
    
    # Memory
    save_policy: str = "save_confirmed"
    memory_trust_level: str = "cautious"
    
    # Explain Mode
    explain_mode: str = "off"  # off, brief, detailed
    
    # Rules
    active_rules: List[str] = None  # List of rule instructions
    
    def __post_init__(self):
        if self.allowed_actions is None:
            self.allowed_actions = ["create_decisions", "link_memories"]
        if self.active_rules is None:
            self.active_rules = []
    
    def get_role_description(self) -> str:
        """Get human-readable role description."""
        roles = {
            "partner_strategic": "Ты — равный партнёр в принятии стратегических решений",
            "analyst_logical": "Ты — логический аналитик, фокусируйся на факты и структуру",
            "coach_socratic": "Ты — коуч в сократическом стиле: задавай вопросы, не давай готовых ответов",
            "recorder_passive": "Ты — пассивный фиксатор: минимальное вмешательство, только записывай",
            "explorer_hypothesis": "Ты — исследователь гипотез: генерируй идеи и предположения",
        }
        return roles.get(self.ai_role, roles["partner_strategic"])
    
    def get_thinking_instruction(self) -> str:
        """Get thinking depth instruction."""
        depths = {
            "shallow": "Отвечай кратко и по делу",
            "structured": "Структурируй ответ логично, выделяй ключевые мысли",
            "systemic": "Анализируй системно, находи взаимосвязи и последствия",
            "philosophical": "Максимальная глубина рефлексии, исследуй корни проблем",
        }
        return depths.get(self.thinking_depth, depths["structured"])
    
    def get_confrontation_instruction(self) -> str:
        """Get confrontation level instruction."""
        levels = {
            "none": "Не спорь с пользователем, всегда соглашайся",
            "soft": "Мягко указывай на возможные проблемы",
            "argumented": "Возражай аргументировано когда видишь логические ошибки",
            "hard": "Жёстко останавливай при серьёзных логических ошибках",
        }
        return levels.get(self.confrontation_level, levels["argumented"])
    
    def get_initiative_instruction(self) -> str:
        """Get initiative level instruction."""
        levels = {
            "request_only": "Отвечай только на прямые вопросы, не проявляй инициативу",
            "suggest": "Предлагай идеи и улучшения когда уместно",
            "warn": "Активно предупреждай о потенциальных проблемах",
            "proactive": "Самостоятельно формируй инсайты и рекомендации",
        }
        return levels.get(self.initiative_level, levels["suggest"])
    
    def get_explain_instruction(self) -> str:
        """Get explain mode instruction."""
        modes = {
            "off": "",
            "brief": (
                "\n\n## Режим Explain (краткий)\n"
                "В конце КАЖДОГО ответа добавляй блок:\n"
                "```\n"
                "💡 Почему так:\n"
                "• [1-2 предложения о логике ответа]\n"
                "```"
            ),
            "detailed": (
                "\n\n## Режим Explain (подробный)\n"
                "В конце КАЖДОГО ответа добавляй блок:\n"
                "```\n"
                "🧠 Объяснение логики:\n"
                "1. Как я понял запрос: [интерпретация]\n"
                "2. Какую стратегию выбрал: [подход]\n"
                "3. Почему именно так: [обоснование]\n"
                "4. Альтернативы: [что ещё можно было]\n"
                "```"
            ),
        }
        return modes.get(self.explain_mode, "")
    
    def get_settings_prompt(self) -> str:
        """Generate system prompt additions based on settings."""
        parts = [
            "",
            "## Настройки поведения",
            "",
            f"### Роль",
            self.get_role_description(),
            "",
            f"### Глубина мышления",
            self.get_thinking_instruction(),
            "",
            f"### Конфронтация",
            self.get_confrontation_instruction(),
            "",
            f"### Инициатива",
            self.get_initiative_instruction(),
        ]
        
        # Add explain mode if enabled
        explain_instruction = self.get_explain_instruction()
        if explain_instruction:
            parts.append(explain_instruction)
        
        # Add rules if any
        if self.active_rules:
            parts.extend([
                "",
                "## Персональные правила пользователя",
                "ОБЯЗАТЕЛЬНО соблюдай эти правила:",
                "",
            ])
            for i, rule in enumerate(self.active_rules, 1):
                parts.append(f"{i}. {rule}")
        
        return "\n".join(parts)


async def get_user_settings(
    db: AsyncSession,
    user_id: UUID,
) -> UserSettingsContext:
    """
    Load user settings from database.
    Returns default settings if none exist.
    """
    try:
        # Load settings
        result = await db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        
        # Load active rules
        rules_result = await db.execute(
            select(Rule).where(
                Rule.user_id == user_id,
                Rule.is_active == True
            ).order_by(Rule.sort_order)
        )
        rules = rules_result.scalars().all()
        
        if not settings:
            # Return defaults with rules
            return UserSettingsContext(
                active_rules=[r.instruction for r in rules]
            )
        
        return UserSettingsContext(
            ai_role=settings.ai_role or "partner_strategic",
            thinking_depth=settings.thinking_depth or "structured",
            response_style=settings.response_style or "detailed",
            confrontation_level=settings.confrontation_level or "argumented",
            initiative_level=settings.initiative_level or "suggest",
            intervention_frequency=settings.intervention_frequency or "realtime",
            allowed_actions=settings.allowed_actions or ["create_decisions", "link_memories"],
            save_policy=settings.save_policy or "save_confirmed",
            memory_trust_level=settings.memory_trust_level or "cautious",
            explain_mode=getattr(settings, 'explain_mode', None) or "off",
            active_rules=[r.instruction for r in rules],
        )
        
    except Exception as e:
        logger.error("failed_to_load_settings", error=str(e), user_id=str(user_id))
        return UserSettingsContext()  # Return defaults
