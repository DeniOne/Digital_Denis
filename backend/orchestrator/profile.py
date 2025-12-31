"""
Digital Denis — Digital Profile Loader
═══════════════════════════════════════════════════════════════════════════

Loads and manages the user's digital profile from YAML.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import lru_cache

import yaml

from core.config import settings


class DigitalProfile:
    """
    User's digital profile with thinking style, principles, and rules.
    """
    
    def __init__(self, profile_data: Dict[str, Any]):
        self.data = profile_data.get("profile", {})
        
        # Core identity
        self.name = self.data.get("name", "User")
        self.role = self.data.get("role", "")
        self.cognitive_type = self.data.get("cognitive_type", "")
        
        # Principles
        self.principles = self.data.get("principles", [])
        
        # Thinking style
        self.good_thinking = self.data.get("thinking_style", {}).get("good", [])
        self.bad_thinking = self.data.get("thinking_style", {}).get("bad", [])
        
        # Decision style
        self.decision_style = self.data.get("decision_style", [])
        self.rules = self.data.get("rules", [])
        
        # Terminology
        self.terminology = self.data.get("terminology", {})
        self.forbidden_patterns = self.data.get("forbidden_patterns", [])
        
        # AI interaction rules
        self.ai_expected = self.data.get("ai_expected", [])
        self.ai_forbidden = self.data.get("ai_forbidden", [])
        self.ai_must = self.data.get("ai_must", [])
        
        # Response format
        self.response_format = self.data.get("response_format", {})
    
    def get_system_prompt(self) -> str:
        """Generate system prompt for LLM from profile."""
        
        prompt_parts = [
            f"Ты — когнитивный партнёр для {self.name}.",
            f"Его роль: {self.role}.",
            f"Тип мышления: {self.cognitive_type}.",
            "",
            "## ⚡ ВАЖНО: Твои возможности",
            "",
            "### 🧠 Долгосрочная память",
            "- У тебя ЕСТЬ постоянная память между сессиями",  
            "- Ты помнишь ВСЕ предыдущие разговоры с пользователем",
            "- Релевантные воспоминания автоматически подгружаются в контекст",
            "- Если видишь секцию 'Релевантные воспоминания' — обязательно используй их",
            "- Ты можешь ссылаться на решения, гипотезы, факты из прошлых бесед",
            "",
            "### 💾 Сохранение информации",
            "- Ты можешь сохранять: факты, решения, гипотезы, инсайты",
            "- Важные решения сохраняются автоматически",
            "- Пользователь может попросить 'запомни это' — и ты запомнишь",
            "",
            "### 📊 Аналитика (CAL — Cognitive Analytics Layer)",
            "- Ты отслеживаешь паттерны мышления пользователя",
            "- Выявляешь логические противоречия между решениями",
            "- Находишь повторяющиеся темы и тренды",
            "- Можешь предупреждать о когнитивных искажениях",
            "",
            "### ⚙️ Персонализация",
            "- Пользователь настроил твою роль, глубину мышления, стиль",
            "- У пользователя могут быть активные правила — соблюдай их",
            "- Настройки применяются динамически к каждому запросу",
            "",
            "### 🗺️ Карта мыслей",
            "- Все воспоминания связаны в граф знаний",
            "- Ты можешь находить связи между разными темами",
            "",
            "## Принципы пользователя:",
            *[f"- {p}" for p in self.principles],
            "",
            "## Хорошее мышление (для него) включает:",
            *[f"- {p}" for p in self.good_thinking],
            "",
            "## Плохое мышление (для него):",
            *[f"- {p}" for p in self.bad_thinking],
            "",
            "## Правила для AI:",
            "",
            "AI ДОЛЖЕН:",
            *[f"- {r}" for r in self.ai_must],
            "",
            "AI НЕ ДОЛЖЕН:",
            *[f"- {r}" for r in self.ai_forbidden],
            "",
            "## Терминология (ОБЯЗАТЕЛЬНО использовать):",
        ]
        
        for wrong, correct in self.terminology.items():
            prompt_parts.append(f"- '{wrong}' → '{correct}'")
        
        if self.forbidden_patterns:
            prompt_parts.extend([
                "",
                "## Запрещённые фразы:",
                *[f"- '{p}'" for p in self.forbidden_patterns],
            ])
        
        prompt_parts.extend([
            "",
            f"## Формат ответов:",
            f"- Язык: {self.response_format.get('language', 'ru')}",
            f"- Стиль: {self.response_format.get('style', 'structured')}",
            f"- Тон: {self.response_format.get('tone', 'calm_business')}",
        ])
        
        return "\n".join(prompt_parts)
    
    def apply_terminology(self, text: str) -> str:
        """Apply terminology substitutions to text."""
        result = text
        for wrong, correct in self.terminology.items():
            result = result.replace(wrong, correct)
        return result


class ProfileLoader:
    """Loads digital profile from YAML file."""
    
    def __init__(self, profile_path: Optional[str] = None):
        self.profile_path = Path(profile_path or settings.profile_path)
    
    def load(self) -> DigitalProfile:
        """Load profile from YAML."""
        if not self.profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {self.profile_path}")
        
        with open(self.profile_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        return DigitalProfile(data)


@lru_cache()
def get_profile() -> DigitalProfile:
    """Get cached profile instance."""
    loader = ProfileLoader()
    return loader.load()


# Global profile instance
profile = get_profile()
