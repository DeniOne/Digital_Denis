"""
Digital Den — Conversation State Repository
═══════════════════════════════════════════════════════════════════════════

CRUD операции для Conversation State.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from memory.models import ConversationState


class ConversationStateRepository:
    """
    Repository для работы с Conversation State.
    """
    
    async def get_by_conversation_id(
        self,
        db: AsyncSession,
        user_id: UUID,
        conversation_id: str
    ) -> Optional[ConversationState]:
        """
        Получить Conversation State по conversation_id.
        
        Args:
            db: Database session
            user_id: ID пользователя
            conversation_id: ID разговора (например, chat_id из Telegram)
            
        Returns:
            ConversationState или None
        """
        stmt = select(ConversationState).where(
            ConversationState.user_id == user_id,
            ConversationState.conversation_id == conversation_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def upsert(
        self,
        db: AsyncSession,
        user_id: UUID,
        conversation_id: str,
        state_data: Dict
    ) -> ConversationState:
        """
        Создать или обновить Conversation State.
        
        Args:
            db: Database session
            user_id: ID пользователя
            conversation_id: ID разговора
            state_data: Данные состояния (dict из State Extractor)
            
        Returns:
            Обновлённый ConversationState
        """
        # Подготовка данных
        insert_data = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "topic": state_data.get("topic"),
            "goal": state_data.get("goal"),
            "current_step": state_data.get("current_step"),
            "intent": state_data.get("intent"),
            "active_entities": state_data.get("active_entities", []),
            "active_objects": state_data.get("active_objects", []),
            "assumptions": state_data.get("assumptions", []),
            "constraints": state_data.get("constraints", []),
            "decisions_made": state_data.get("decisions_made", []),
            "open_questions": state_data.get("open_questions", []),
            "unresolved_points": state_data.get("unresolved_points", []),
            "confidence_level": state_data.get("confidence_level", "unknown"),
            "last_updated": datetime.utcnow(),
        }
        
        # UPDATE данные (всё кроме user_id и conversation_id)
        update_data = {k: v for k, v in insert_data.items() if k not in ["user_id", "conversation_id"]}
        
        # PostgreSQL-specific UPSERT
        stmt = (
            insert(ConversationState)
            .values(**insert_data)
            .on_conflict_do_update(
                constraint="uq_user_conversation",
                set_=update_data
            )
            .returning(ConversationState)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.scalar_one()
    
    async def delete_by_conversation_id(
        self,
        db: AsyncSession,
        user_id: UUID,
        conversation_id: str
    ) -> bool:
        """
        Удалить Conversation State.
        
        Returns:
            True если удалено, False если не найдено
        """
        stmt = delete(ConversationState).where(
            ConversationState.user_id == user_id,
            ConversationState.conversation_id == conversation_id
        )
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount > 0
    
    async def cleanup_expired(self, db: AsyncSession) -> int:
        """
        Удалить Conversation States с истекшим TTL.
        
        Returns:
            Количество удалённых записей
        """
        # Удаляем те, где last_updated + ttl_hours < now
        # SQL: WHERE last_updated < NOW() - INTERVAL '1 hour' * ttl_hours
        
        stmt = delete(ConversationState).where(
            ConversationState.last_updated < (
                datetime.utcnow() - timedelta(hours=1) * ConversationState.ttl_hours
            )
        )
        
        result = await db.execute(stmt)
        deleted_count = result.rowcount
        
        await db.commit()
        
        print(f"[ConversationState] Deleted {deleted_count} expired states")
        return deleted_count


# Global instance
conversation_state_repo = ConversationStateRepository()
