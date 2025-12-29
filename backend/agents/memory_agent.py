"""
Digital Denis — Memory Agent
═══════════════════════════════════════════════════════════════════════════

Agent responsible for memory operations: saving, retrieving, managing.
"""

from typing import Optional, Dict, Any
from uuid import UUID

from agents.base import BaseAgent, AgentContext, AgentResponse
from memory.long_term import long_term_memory
from llm.groq import groq


class MemoryAgent(BaseAgent):
    """
    Memory Agent — управляет памятью.
    
    Ответственности:
    - Сохранение решений, инсайтов, фактов
    - Поиск релевантных воспоминаний
    - Агрегация похожего контента
    - Управление забыванием
    """
    
    name = "memory"
    description = "Memory management agent"
    participates_in_dialogue = False
    writes_to_memory = True
    is_synchronous = True
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """Process memory-related request."""
        
        # This agent is typically called after other agents
        # to save their outputs
        return AgentResponse(
            content="Memory operation completed",
            agent=self.name,
            save_to_memory=False,
        )
    
    async def save_from_response(
        self,
        db,
        response: AgentResponse,
        session_id: UUID,
        user_message: str,
    ) -> Optional[UUID]:
        """
        Save memory item from agent response.
        
        Called after agent processes a request if save_to_memory=True.
        """
        if not response.save_to_memory:
            return None
        
        # Generate summary using cheap LLM
        summary = await self._generate_summary(
            user_message,
            response.content,
            response.memory_type or "thought"
        )
        
        # Prepare structured data for decisions
        structured_data = None
        if response.memory_type == "decision":
            structured_data = await self._extract_decision_structure(
                user_message,
                response.content
            )
        
        # Save to long-term memory
        item = await long_term_memory.save(
            db=db,
            item_type=response.memory_type or "thought",
            content=f"User: {user_message}\n\nAssistant: {response.content}",
            summary=summary,
            structured_data=structured_data,
            source_agent=response.agent,
            source_session=session_id,
            confidence=response.confidence,
        )
        
        return item.id
    
    async def _generate_summary(
        self,
        user_message: str,
        response: str,
        memory_type: str,
    ) -> str:
        """Generate short summary using cheap LLM."""
        
        prompt = f"""Создай краткое резюме (1-2 предложения) этого диалога.
Тип: {memory_type}

User: {user_message[:500]}
Assistant: {response[:500]}

Резюме:"""
        
        try:
            summary = await groq.complete_simple(prompt)
            return summary.strip()[:300]
        except Exception:
            return f"[{memory_type}] {user_message[:100]}..."
    
    async def _extract_decision_structure(
        self,
        user_message: str,
        response: str,
    ) -> Dict[str, Any]:
        """Extract structured data from decision."""
        
        prompt = f"""Извлеки структуру решения из текста. Верни JSON:
{{
  "hypothesis": "что решается",
  "decision": "принятое решение",
  "reasons": ["причина 1", "причина 2"],
  "risks": ["риск 1"],
  "next_steps": ["шаг 1"]
}}

Текст:
User: {user_message[:300]}
Assistant: {response[:500]}

JSON:"""
        
        try:
            result = await groq.complete_simple(prompt)
            # Simple JSON extraction (could use proper parsing)
            import json
            # Try to find JSON in response
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except Exception:
            pass
        
        return {"raw": response[:200]}
    
    async def get_context_memories(
        self,
        db,
        user_message: str,
        limit: int = 5,
    ) -> list:
        """Get relevant memories for context."""
        
        # Simple search for now (will be replaced with semantic search)
        memories = await long_term_memory.search(
            db=db,
            query_text=user_message[:100],
            limit=limit,
        )
        
        return [
            {
                "id": str(m.id),
                "item_type": m.item_type,
                "content": m.content,
                "summary": m.summary,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in memories
        ]


# Global instance
memory_agent = MemoryAgent()
