"""
Digital Den — RAG 2.0 Ranking Configuration
═══════════════════════════════════════════════════════════════════════════

Весовые коэффициенты для intent-aware ранжирования памяти.
"""

from datetime import datetime
from typing import Dict

# ═══════════════════════════════════════════════════════════════════════════
# Memory Type Weights по Intent
# ═══════════════════════════════════════════════════════════════════════════

MEMORY_TYPE_WEIGHTS: Dict[str, Dict[str, float]] = {
    # Запрос на принятие решения
    "decision_request": {
        "principle": 1.5,      # Принципы критичны для решений
        "rule": 1.5,           # Правила определяют ограничения
        "decision": 1.2,       # Прошлые решения — опыт
        "fact": 1.0,           # Факты поддерживают решения
        "hypothesis": 0.5,     # Гипотезы менее надёжны
        "reflection": 0.3,     # Рефлексии второстепенны
        "emotion": 0.1,        # Эмоции не должны влиять на решения
        "failure": 0.8,        # Ошибки важны для предотвращения
        "task": 0.6,           # Задачи умеренно релевантны
        "insight": 0.9,        # Инсайты могут быть полезны
        "thought": 0.7,        # Мысли менее приоритетны
    },
    
    # Анализ ситуации
    "analysis": {
        "fact": 1.5,           # Факты — основа анализа
        "decision": 1.2,       # Решения показывают паттерны
        "reflection": 1.0,     # Рефлексии дают context
        "hypothesis": 0.8,     # Гипотезы могут быть релевантны
        "principle": 0.7,      # Принципы менее критичны
        "failure": 1.3,        # Ошибки очень важны для анализа
        "insight": 1.1,        # Инсайты помогают понять
        "emotion": 0.4,        # Эмоции второстепенны
        "rule": 0.6,           # Правила не так важны
        "task": 0.5,           # Задачи не очень релевантны
        "thought": 0.9,        # Мысли могут быть полезны
    },
    
    # Проверка фактов
    "fact_check": {
        "fact": 2.0,           # Факты — максимальный приоритет
        "principle": 1.0,      # Принципы могут подтверждать
        "decision": 0.5,       # Решения менее релевантны
        "hypothesis": 0.2,     # Гипотезы не подходят
        "reflection": 0.3,     # Рефлексии не факты
        "emotion": 0.1,        # Эмоции не факты
        "rule": 0.8,           # Правила могут быть фактами
        "failure": 0.4,        # Ошибки не подходят
        "task": 0.3,           # Задачи не релевантны
        "insight": 0.7,        # Инсайты умеренно полезны
        "thought": 0.4,        # Мысли не факты
    },
    
    # Планирование
    "planning": {
        "principle": 1.3,      # Принципы задают direction
        "rule": 1.2,           # Правила определяют constraints
        "decision": 1.1,       # Прошлые решения — опыт
        "task": 1.4,           # Задачи очень релевантны
        "fact": 1.0,           # Факты поддерживают план
        "hypothesis": 0.7,     # Гипотезы могут быть полезны
        "reflection": 0.6,     # Рефлексии умеренно полезны
        "emotion": 0.2,        # Эмоции не важны
        "failure": 0.9,        # Ошибки помогают избежать повторений
        "insight": 1.0,        # Инсайты полезны
        "thought": 0.8,        # Мысли второстепенны
    },
    
    # Рефлексия
    "reflection": {
        "reflection": 1.5,     # Прошлые рефлексии очень важны
        "emotion": 1.2,        # Эмоции релевантны для рефлексии
        "decision": 1.0,       # Решения показывают паттерны
        "hypothesis": 0.9,     # Гипотезы могут быть интересны
        "fact": 0.8,           # Факты менее критичны
        "principle": 0.7,      # Принципы второстепенны
        "failure": 1.1,        # Ошибки важны для саморефлексии
        "insight": 1.3,        # Инсайты очень важны
        "rule": 0.5,           # Правила не так важны
        "task": 0.4,           # Задачи не релевантны
        "thought": 1.2,        # Мысли важны для рефлексии
    },
    
    # Kaizen review (анализ прогресса)
    "kaizen_review": {
        "decision": 1.5,       # Решения показывают прогресс
        "reflection": 1.4,     # Рефлексии ключевые
        "principle": 1.2,      # Принципы определяют стандарты
        "fact": 1.0,           # Факты подтверждают прогресс
        "failure": 1.3,        # Ошибки показывают learning
        "insight": 1.4,        # Инсайты демонстрируют рост
        "hypothesis": 0.6,     # Гипотезы менее важны
        "emotion": 0.8,        # Эмоции умеренно релевантны
        "task": 0.9,           # Задачи показывают execution
        "rule": 0.7,           # Правила второстепенны
        "thought": 1.0,        # Мысли показывают clarity
    },
    
    # Обычный разговор
    "casual": {
        "fact": 1.0,           # Все типы равноценны
        "decision": 1.0,
        "principle": 1.0,
        "rule": 1.0,
        "hypothesis": 1.0,
        "reflection": 1.0,
        "emotion": 1.0,
        "failure": 1.0,
        "task": 1.0,
        "insight": 1.0,
        "thought": 1.0,
    },
}

# Базовый вес intent (можно варьировать по критичности)
INTENT_BASE_WEIGHT = 1.0


# ═══════════════════════════════════════════════════════════════════════════
# Time Decay Function
# ═══════════════════════════════════════════════════════════════════════════

def calculate_time_decay(
    memory_type: str,
    created_at: datetime,
    now: datetime = None
) -> float:
    """
    Вычисляет коэффициент временной деградации памяти.
    
    Правила:
    - principle, rule → decay ≈ 1 (не деградируют)
    - fact → слабый decay (0.95 через год)
    - decision → средний decay (0.90 через год)
    - reflection, hypothesis → сильный decay (0.5 через 6 месяцев)
    - emotion, failure → очень сильный decay (0.3 через 3 месяца)
    
    Args:
        memory_type: Тип памяти (principle, fact, decision, etc.)
        created_at: Дата создания воспоминания
        now: Текущая дата (опционально, по умолчанию utcnow)
        
    Returns:
        float: Коэффициент decay (0.0 - 1.0)
    """
    if now is None:
        now = datetime.utcnow()
    
    # Убедимся, что created_at timezone-aware or timezone-naive совпадают
    if created_at.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=created_at.tzinfo)
    elif created_at.tzinfo is None and now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    
    age_days = (now - created_at).days
    
    # Принципы и правила не деградируют
    if memory_type in ["principle", "rule"]:
        return 1.0
    
    # Факты: слабый decay (-5% в год)
    elif memory_type == "fact":
        decay_rate = 0.05 / 365  # 0.05 за год
        decay = 1.0 - (age_days * decay_rate)
        return max(0.8, decay)  # минимум 0.8
    
    # Решения: средний decay (-10% в год)
    elif memory_type == "decision":
        decay_rate = 0.10 / 365
        decay = 1.0 - (age_days * decay_rate)
        return max(0.7, decay)  # минимум 0.7
    
    # Инсайты: слабый decay (похоже на факты)
    elif memory_type == "insight":
        decay_rate = 0.07 / 365
        decay = 1.0 - (age_days * decay_rate)
        return max(0.75, decay)
    
    # Рефлексии и гипотезы: сильный decay (-50% через 6 месяцев)
    elif memory_type in ["reflection", "hypothesis"]:
        decay_rate = 0.50 / 180  # 0.50 за 6 месяцев
        decay = 1.0 - (age_days * decay_rate)
        return max(0.3, decay)  # минимум 0.3
    
    # Эмоции и ошибки: очень сильный decay (-70% через 3 месяца)
    elif memory_type in ["emotion", "failure"]:
        decay_rate = 0.70 / 90  # 0.70 за 3 месяца
        decay = 1.0 - (age_days * decay_rate)
        return max(0.2, decay)  # минимум 0.2
    
    # Задачи: средний decay (как decisions)
    elif memory_type == "task":
        decay_rate = 0.10 / 365
        decay = 1.0 - (age_days * decay_rate)
        return max(0.7, decay)
    
    # Мысли: сильный decay (как reflections)
    elif memory_type == "thought":
        decay_rate = 0.50 / 180
        decay = 1.0 - (age_days * decay_rate)
        return max(0.3, decay)
    
    # Fallback: нет decay
    else:
        return 1.0


# ═══════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════

def get_memory_weight(memory_type: str, intent: str) -> float:
    """
    Получить вес типа памяти для данного интента.
    
    Args:
        memory_type: Тип памяти
        intent: Intent пользователя
        
    Returns:
        float: Весовой коэффициент
    """
    weights = MEMORY_TYPE_WEIGHTS.get(intent, MEMORY_TYPE_WEIGHTS["casual"])
    return weights.get(memory_type, 1.0)
