"""
Digital Den — Operator Agent
═══════════════════════════════════════════════════════════════════════════

Agent for converting ideas and decisions into actionable plans.
"""

from typing import Optional, List, Dict, Any

from agents.base import BaseAgent, AgentContext, AgentResponse
from llm.openrouter import openrouter
from llm.base import LLMMessage


class OperatorAgent(BaseAgent):
    """
    Operator Agent — операционный агент.
    
    Ответственности:
    - Превращение идей в задачи
    - Создание планов действий
    - Формирование чеклистов
    - Построение таймлайнов
    
    Особенности:
    - Всегда выдаёт структурированные планы
    - Не выполняет действия автоматически
    - Требует подтверждения на критические шаги
    """
    
    name = "operator"
    description = "Ideas to actions agent"
    participates_in_dialogue = True
    writes_to_memory = True
    is_synchronous = True
    
    OPERATOR_SYSTEM_PROMPT = """Ты — операционный модуль системы Digital Den.

Твоя специализация:
- Превращение идей в конкретные задачи
- Создание пошаговых планов
- Формирование чеклистов
- Определение сроков и ответственных

Правила работы:
1. ВСЕГДА выдавай структурированный план
2. Каждый шаг должен быть конкретным и измеримым
3. Указывай ориентировочные сроки
4. Помечай критические шаги ⚠️
5. Группируй задачи логически
6. НЕ выполняй действия — только планируй

Форматы вывода:

### Чеклист:
- [ ] Задача 1
- [ ] Задача 2 (зависит от 1)

### План с таймлайном:
| Этап | Задача | Срок | Статус |
|------|--------|------|--------|

### Step-by-step:
1. **Шаг 1:** Действие
   - Подзадача 1.1
   - Подзадача 1.2
"""
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """Process operational request."""
        
        # Build messages
        messages = [
            LLMMessage(role="system", content=context.system_prompt),
            LLMMessage(role="system", content=self.OPERATOR_SYSTEM_PROMPT),
        ]
        
        # Add relevant decisions/ideas from memory
        if context.memories:
            ideas_context = self._format_ideas(context.memories)
            messages.append(LLMMessage(
                role="system",
                content=f"Связанные решения и идеи:\n{ideas_context}"
            ))
        
        # Add chat history (longer for operational context)
        for msg in context.history[-8:]:
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
        
        # Plans are usually saved
        save_to_memory = self._is_actionable_plan(response.content)
        
        return AgentResponse(
            content=response.content,
            agent=self.name,
            save_to_memory=save_to_memory,
            memory_type="decision" if save_to_memory else None,
            confidence=0.7,
            tokens_used=response.tokens_used,
        )
    
    def _format_ideas(self, memories: List[Dict]) -> str:
        """Format memories with decisions and ideas."""
        if not memories:
            return "Нет связанных идей."
        
        # Prioritize decisions and insights
        priority_types = ["decision", "insight"]
        sorted_mems = sorted(
            memories,
            key=lambda x: (x.get("item_type") in priority_types, x.get("created_at", "")),
            reverse=True
        )
        
        parts = []
        for mem in sorted_mems[:5]:
            mem_type = mem.get("item_type", "idea")
            content = mem.get("content", "")[:200]
            parts.append(f"[{mem_type}] {content}")
        
        return "\n".join(parts)
    
    def _is_actionable_plan(self, response: str) -> bool:
        """Check if response contains actionable plan."""
        plan_indicators = [
            "- [ ]",  # Checklist
            "| этап |", "| шаг |",  # Table
            "1. **", "## шаг 1", "## этап 1",  # Numbered steps
            "план:", "план действий",
            "чеклист:", "checklist:",
        ]
        
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in plan_indicators)


# Global instance
operator_agent = OperatorAgent()
