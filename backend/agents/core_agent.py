"""
Digital Den — Core Agent
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
    - Ведёт диалог от лица Digital Den
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
        user_msg_with_guard = context.user_message
        if not context.history:
            # Special instruction if history is empty to prevent jumping to conclusions based on partial RAG
            user_msg_with_guard = (
                f"[SYSTEM NOTE: Диалог только начался, истории сообщений нет. "
                f"Будь осторожен с выводами, основываясь только на отрывочных воспоминаниях.]\n"
                f"{context.user_message}"
            )
            
        messages.append(LLMMessage(
            role="user",
            content=user_msg_with_guard
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # Hybrid AI: Use LLM Selector for automatic model selection
        # ═══════════════════════════════════════════════════════════════════
        from llm.llm_selector import llm_selector, ModelRole
        
        # Determine model role from context
        model_role_str = context.model_role or "default"
        try:
            model_role = ModelRole(model_role_str)
        except ValueError:
            model_role = ModelRole.DEFAULT
        
        # Fallback chain: THINKING -> DEFAULT -> FAST
        fallback_role = ModelRole.DEFAULT if model_role == ModelRole.THINKING else ModelRole.FAST
        
        try:
            response = await llm_selector.complete(
                role=model_role,
                messages=messages,
                fallback_role=fallback_role,
            )
        except Exception as e:
            # Ultimate fallback to Groq if everything fails
            import logging
            from llm.groq import groq
            logging.warning(f"LLM Selector failed, falling back to Groq: {e}")
            response = await groq.complete(messages)
        
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
            "цель", "моя цель", "жизненная цель",
        ]
        
        # Insight/Fact indicators
        insight_keywords = [
            "понял", "осознал", "вывод",
            "инсайт", "понимаю теперь",
            "ключевой момент", "важно что",
            "принцип", "мое правило", "убеждение",
            "ценность", "идеал", "миссия",
        ]
        
        # Personal/Family facts - ВСЕГДА сохраняем!
        personal_keywords = [
            "внук", "внучк", "сын", "дочь", "дочер", "ребенок", "ребёнок", "дети",
            "жена", "муж", "супруг", "родител", "мама", "папа", "отец", "мать",
            "брат", "сестр", "бабушк", "дедушк", "семь",
            "день рождения", "родился", "родилась",
            "зовут", "имя моего", "имя моей",
            "мне лет", "моих лет", "я родился", "я родилась",
            "живу в", "работаю", "моя работа", "моя профессия",
            "хобби", "увлечени", "люблю делать",
        ]
        
        for keyword in decision_keywords:
            if keyword in combined:
                return True, "decision"
        
        for keyword in insight_keywords:
            if keyword in combined:
                return True, "insight"
        
        for keyword in personal_keywords:
            if keyword in combined:
                return True, "fact"  # Сохраняем как факт
        
        return False, None


# Global instance
core_agent = CoreAgent()
