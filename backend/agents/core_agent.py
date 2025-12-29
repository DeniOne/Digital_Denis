"""
Digital Denis — Core Agent
═══════════════════════════════════════════════════════════════════════════

Main dialogue agent that embodies the user's thinking style.
"""

from typing import Optional

from agents.base import BaseAgent, AgentContext, AgentResponse
from llm.openrouter import openrouter
from llm.base import LLMMessage


class CoreAgent(BaseAgent):
    """
    Core Agent — главный диалоговый агент.
    
    Ответственности:
    - Ведёт диалог от лица Digital Denis
    - Применяет профиль пользователя
    - Структурирует мышление
    - Идентифицирует решения для сохранения
    """
    
    name = "core"
    description = "Main dialogue agent"
    participates_in_dialogue = True
    writes_to_memory = True
    is_synchronous = True
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """Process user message and generate response."""
        
        # Build messages for LLM
        messages = [
            LLMMessage(role="system", content=context.system_prompt),
        ]
        
        # Add relevant memories to context
        if context.memories:
            memory_context = self._format_memories(context.memories)
            messages.append(LLMMessage(
                role="system",
                content=f"Релевантные воспоминания:\n{memory_context}"
            ))
        
        # Add chat history
        for msg in context.history[-10:]:  # Last 10 messages
            messages.append(LLMMessage(
                role=msg["role"],
                content=msg["content"]
            ))
        
        # Add current user message
        messages.append(LLMMessage(
            role="user",
            content=context.user_message
        ))
        
        # Call LLM
        response = await openrouter.complete(messages)
        
        # Check if response contains a decision
        save_to_memory, memory_type = self._should_save(
            context.user_message,
            response.content
        )
        
        return AgentResponse(
            content=response.content,
            agent=self.name,
            save_to_memory=save_to_memory,
            memory_type=memory_type,
            confidence=0.8,
            tokens_used=response.tokens_used,
        )
    
    def _format_memories(self, memories: list) -> str:
        """Format memories for context."""
        if not memories:
            return ""
        
        parts = []
        for mem in memories[:5]:  # Limit to 5 memories
            mem_type = mem.get("item_type", "thought")
            content = mem.get("content", "")[:200]
            parts.append(f"[{mem_type}] {content}")
        
        return "\n".join(parts)
    
    def _should_save(self, user_message: str, response: str) -> tuple[bool, Optional[str]]:
        """
        Determine if this exchange should be saved to memory.
        
        Returns: (should_save, memory_type)
        """
        combined = (user_message + " " + response).lower()
        
        # Decision indicators
        decision_keywords = [
            "решил", "решение", "решаю",
            "принимаю", "принял решение",
            "выбираю", "выбор сделан",
            "буду делать", "будем делать",
            "утверждаю", "одобряю",
        ]
        
        # Insight indicators
        insight_keywords = [
            "понял", "осознал", "вывод",
            "инсайт", "понимаю теперь",
            "ключевой момент", "важно что",
        ]
        
        for keyword in decision_keywords:
            if keyword in combined:
                return True, "decision"
        
        for keyword in insight_keywords:
            if keyword in combined:
                return True, "insight"
        
        return False, None


# Global instance
core_agent = CoreAgent()
