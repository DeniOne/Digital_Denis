"""
Digital Denis — Analyst Agent
═══════════════════════════════════════════════════════════════════════════

Agent for data analysis, numbers, and logical constructions.
"""

from typing import Optional, List, Dict, Any

from agents.base import BaseAgent, AgentContext, AgentResponse
from llm.openrouter import openrouter
from llm.base import LLMMessage


class AnalystAgent(BaseAgent):
    """
    Analyst Agent — аналитический агент.
    
    Ответственности:
    - Анализ цифр и данных
    - Экономические расчёты
    - Логический анализ
    - Выявление паттернов в данных
    
    Особенности:
    - Предпочитает таблицы и структурированные данные
    - Разделяет факты, допущения и выводы
    - Явно указывает на недостаток данных
    """
    
    name = "analyst"
    description = "Data and logic analysis agent"
    participates_in_dialogue = True
    writes_to_memory = True
    is_synchronous = True
    
    ANALYST_SYSTEM_PROMPT = """Ты — аналитический модуль системы Digital Denis.

Твоя специализация:
- Анализ цифр, метрик и данных
- Экономические и финансовые расчёты
- Логический анализ аргументов
- Выявление паттернов и трендов

Правила работы:
1. ВСЕГДА разделяй: Факты | Допущения | Выводы
2. Предпочитай таблицы и структурированные форматы
3. Если данных недостаточно — явно укажи это
4. Не делай предположений без оснований
5. Приводи расчёты пошагово
6. Указывай погрешность и ограничения анализа

Формат ответа:
## Входные данные
[что получено для анализа]

## Анализ
[пошаговый анализ]

## Выводы
[ключевые выводы]

## Ограничения
[если есть недостаток данных или неточности]
"""
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """Process analytical request."""
        
        # Build messages
        messages = [
            LLMMessage(role="system", content=context.system_prompt),
            LLMMessage(role="system", content=self.ANALYST_SYSTEM_PROMPT),
        ]
        
        # Add relevant memories (data context)
        if context.memories:
            data_context = self._format_data_context(context.memories)
            messages.append(LLMMessage(
                role="system",
                content=f"Имеющиеся данные из памяти:\n{data_context}"
            ))
        
        # Add chat history
        for msg in context.history[-5:]:  # Shorter history for analyst
            messages.append(LLMMessage(
                role=msg["role"],
                content=msg["content"]
            ))
        
        # Add user request
        messages.append(LLMMessage(
            role="user",
            content=context.user_message
        ))
        
        # Call LLM
        response = await openrouter.complete(messages)
        
        # Analyst often produces insights
        save_to_memory, memory_type = self._analyze_for_insights(response.content)
        
        return AgentResponse(
            content=response.content,
            agent=self.name,
            save_to_memory=save_to_memory,
            memory_type=memory_type,
            confidence=0.75,
            tokens_used=response.tokens_used,
        )
    
    def _format_data_context(self, memories: List[Dict]) -> str:
        """Format memories as data context for analysis."""
        if not memories:
            return "Нет данных в памяти."
        
        parts = []
        for mem in memories[:5]:
            mem_type = mem.get("item_type", "data")
            content = mem.get("content", "")[:300]
            created = mem.get("created_at", "")
            parts.append(f"[{mem_type}] ({created})\n{content}")
        
        return "\n---\n".join(parts)
    
    def _analyze_for_insights(self, response: str) -> tuple[bool, Optional[str]]:
        """Determine if analysis contains valuable insights."""
        response_lower = response.lower()
        
        # Key insight indicators
        insight_markers = [
            "ключевой вывод", "важный вывод",
            "обнаружено", "выявлено",
            "паттерн", "тренд",
            "аномалия", "отклонение",
            "рекомендация",
        ]
        
        for marker in insight_markers:
            if marker in response_lower:
                return True, "insight"
        
        # If response has structured conclusions, save as fact
        if "## выводы" in response_lower or "## conclusions" in response_lower:
            return True, "fact"
        
        return False, None


# Global instance
analyst_agent = AnalystAgent()
