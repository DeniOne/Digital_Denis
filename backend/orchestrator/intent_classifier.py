"""
Digital Den — Intent Classifier
═══════════════════════════════════════════════════════════════════════════

Определяет intent пользовательского сообщения для intent-aware RAG.
"""

from typing import Optional

from memory.models import ConversationState


# Список интентов RAG 2.0
INTENTS = [
    "decision_request",   # Запрос на помощь в принятии решения
    "analysis",           # Анализ ситуации / проблемы
    "fact_check",         # Проверка факта или информации
    "planning",           # Планирование действий / стратегии
    "reflection",         # Рефлексия, размышления
    "kaizen_review",      # Анализ прогресса / качества мышления
    "casual",             # Обычный разговор
]


class IntentClassifier:
    """
    Определяет intent пользовательского сообщения.
    
    Использует эвристический подход (keywords + context).
    В будущем можно добавить LLM-based классификацию.
    """
    
    KEYWORDS = {
        "schedule": [
            "напомни", "напомню", "напоминание", "поставь в расписание", "добавь в календарь",
            "событие", "встреча", "созвон", "задача", "дедлайн",
            "через час", "через минут", "завтра в", "в понедельник", "в пятницу",
            "каждый день", "ежедневно", "по будням",
            "день рождения", "поздравить", "не забыть",
            "запланируй", "запланировать", "назначь",
            "напомни мне", "напоминалка", "alarm", "timer",
            "в 10:00", "в 15:30", "в 11:", "в 12:", "в 13:", "в 14:", "в 15:", "в 16:", "в 17:", "в 18:", "в 19:", "в 20:",
            "утром", "вечером", "днём",
            "отмени", "удали", "забудь", "убери", "удалить", "отменить",
            "родился", "родилась", "день рождения", "рождения",
            "таблетку", "таблетка", "лекарство", "лекарства", "выпить", "принять",
        ],
        "memory": [
            "вспомни", "что я говорил", "что мы обсуждали", "помнишь",
            "история разговоров", "найди в памяти", "поиск в памяти",
            "о чём мы говорили", "прошлый разговор", "ранее обсуждали",
            "моя память", "что было", "когда я говорил", "вспомни", "что было",
        ],
        "decision_request": [
            "что делать", "помоги решить", "как поступить", "стоит ли",
            "принять решение", "выбрать", "какой вариант", "что лучше",
            "посоветуй", "как быть", "что выбрать"
        ],
        "analysis": [
            "почему", "как так получилось", "разбери", "проанализируй",
            "в чём причина", "что не так", "объясни", "как это работает",
            "что происходит", "разберись"
        ],
        "fact_check": [
            "это правда", "верно ли", "точно ли", "проверь",
            "правда что", "действительно ли", "подтверди",
            "это так", "уверен что"
        ],
        "planning": [
            "план", "как лучше", "стратегия", "этапы",
            "с чего начать", "проспект", "план действий",
            "распланировать", "организовать", "спланировать"
        ],
        "reflection": [
            "думаю", "размышляю", "замечаю", "наблюдаю",
            "чувствую", "осознаю", "понимаю что",
            "заметил", "интересно что"
        ],
        "kaizen_review": [
            "как я", "мой прогресс", "улучшился ли",
            "стал ли лучше", "моя динамика", "мои результаты",
            "оцени мой прогресс", "как продвигается"
        ],
    }
    
    def classify(
        self,
        message: str,
        conversation_state: Optional[ConversationState] = None
    ) -> str:
        """
        Классифицирует intent пользовательского сообщения.
        
        Args:
            message: Текст сообщения
            conversation_state: Состояние диалога (опционально)
            
        Returns:
            Один из интентов: decision_request, analysis, fact_check, planning, reflection, kaizen_review, casual
        """
        message_lower = message.lower()
        
        # 1. Проверка по ключевым словам
        intent_scores = {}
        for intent, keywords in self.KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Если есть явное совпадение — возвращаем
        if intent_scores:
            # Возвращаем интент с максимальным score
            best_intent = max(intent_scores, key=intent_scores.get)
            return best_intent
        
        # 2. Контекстуальные эвристики
        if conversation_state:
            # Если есть явная цель (goal) — вероятно planning
            if conversation_state.goal and len(conversation_state.goal) > 10:
                return "planning"
            
            # Если есть открытые вопросы — возможно analysis или fact_check
            if conversation_state.open_questions:
                # Проверяем, есть ли в сообщении вопросительные слова
                if any(q in message_lower for q in ["почему", "зачем", "как", "что"]):
                    return "analysis"
                elif any(q in message_lower for q in ["правда", "верно", "точно"]):
                    return "fact_check"
            
            # Если current_step указывает на рефлексию
            if conversation_state.current_step:
                step_lower = conversation_state.current_step.lower()
                if "рефлекс" in step_lower or "размышл" in step_lower:
                    return "reflection"
        
        # 3. Простые эвристики по структуре сообщения
        # Вопросительные предложения
        if "?" in message:
            # Если вопрос начинается с "почему" / "как" — analysis
            if message_lower.strip().startswith(("почему", "как", "зачем", "в чём")):
                return "analysis"
            # Если "что делать" / "стоит ли" — decision_request
            elif any(phrase in message_lower for phrase in ["что делать", "стоит ли", "как поступить"]):
                return "decision_request"
        
        # 4. Fallback
        return "casual"


# Global instance
intent_classifier = IntentClassifier()
