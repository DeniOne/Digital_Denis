"""
Digital Den — RAG 2.0 Universal Orchestrator
═══════════════════════════════════════════════════════════════════════════

Universal RAG 2.0 Core для всех каналов (Telegram, Web, Mobile, Voice).
"""

from typing import Optional, List, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import ConversationState
from memory.state_extractor import state_extractor
from memory.conversation_state_repo import conversation_state_repo
from orchestrator.intent_classifier import intent_classifier
from memory.rag2_search import rag2_search_service, detect_conflicts
from orchestrator.context_assembler import context_assembler
from memory.event_tracker import memory_event_tracker


class RAG2Orchestrator:
    """
    Universal RAG 2.0 Orchestrator - ядро мышления для всех каналов.
    
    Channel-agnostic: работает одинаково для Telegram, Web, Mobile, Voice.
    
    Полный flow:
    1. Load Conversation State
    2. State Extractor (обновление CS)
    3. Intent Classifier
    4. RAG 2.0 Retrieval (intent-aware)
    5. Conflict Detection
    6. Context Assembly
    7. LLM Call
    8. Memory Usage Logging
    9. Update Conversation State
    """
    
    async def process_message(
        self,
        db: AsyncSession,
        user_id: UUID,
        chat_id: str,
        message: str,
        recent_messages: List[Dict],  # [{"role": "user|assistant", "content": "..."}]
        user_settings = None,  # UserSettings (опционально)
    ) -> Dict:
        """
        Обработать сообщение через RAG 2.0 pipeline.
        
        Args:
            db: Database session
            user_id: ID пользователя
            chat_id: ID чата (conversation_id)
            message: Текущее сообщение
            recent_messages: Последние сообщения
            user_settings: Настройки пользователя
            
        Returns:
            dict: {
                "response": str,
                "intent": str,
                "conversation_state": dict,
                "memories_used": int
            }
        """
        # 1. Load Conversation State
        conversation_state = await conversation_state_repo.get_by_conversation_id(
            db, user_id, chat_id
        )
        
        # 2. State Extractor: обновить CS
        previous_state_dict = conversation_state.to_dict() if conversation_state else None
        
        updated_state_dict = await state_extractor.extract_state(
            previous_state=previous_state_dict,
            last_messages=recent_messages,
            current_message=message,
            user_id=user_id
        )
        
        # Сохранить обновлённый CS
        conversation_state = await conversation_state_repo.upsert(
            db, user_id, chat_id, updated_state_dict
        )
        
        # 3. Intent Classifier
        intent = intent_classifier.classify(message, conversation_state)
        
        # 4. RAG 2.0 Retrieval (intent-aware)
        relevant_memories = await rag2_search_service.hybrid_search(
            db=db,
            query=message,
            user_id=user_id,
            intent=intent,
            conversation_state=conversation_state,
            limit=10
        )
        
        # 5. Conflict Detection
        memory_items = [mem for mem, score in relevant_memories]
        conflicts = detect_conflicts(memory_items)
        
        # 6. Context Assembly
        framed_context = await context_assembler.assemble_context(
            user_message=message,
            user_settings=user_settings,
            conversation_state=conversation_state,
            relevant_memories=relevant_memories,
            recent_messages=recent_messages,
            conflicts=conflicts
        )
        
        # 7. LLM Call (здесь вызов LLM должен быть сделан через orchestrator/agents)
        # Возвращаем контекст для дальнейшей обработки
        # В production здесь будет реальный вызов LLM
        
        # 8. Memory Usage Logging
        memory_ids = [mem.id for mem in memory_items]
        if memory_ids:
            await memory_event_tracker.log_memory_usage(
                db=db,
                user_id=user_id,
                memory_ids=memory_ids,
                event_type="recalled",
                context=f"Intent: {intent}, Query: {message[:100]}"
            )
            await memory_event_tracker.increment_usage_count(db, memory_ids)
        
        # 9. Return orchestrated result
        return {
            "framed_context": framed_context,
            "intent": intent,
            "conversation_state": conversation_state.to_dict(),
            "memories_used": len(memory_items),
            "conflicts_detected": len(conflicts) if conflicts else 0,
        }


# Global instance
rag2_orchestrator = RAG2Orchestrator()
