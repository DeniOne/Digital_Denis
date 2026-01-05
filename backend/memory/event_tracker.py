"""
Digital Den — Memory Event Tracking Service
═══════════════════════════════════════════════════════════════════════════

Отслеживание использования памяти и её эффективности (Kaizen Engine).
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import MemoryItem, MemoryEvent


class MemoryEventTracker:
    """
    Сервис для логирования событий использования памяти.
    """
    
    async def log_memory_usage(
        self,
        db: AsyncSession,
        user_id: UUID,
        memory_ids: List[UUID],
        event_type: str = "recalled",
        outcome: Optional[str] = None,
        context: Optional[str] = None
    ):
        """
        Записать событие использования памяти.
        
        Args:
            db: Database session
            user_id: ID пользователя
            memory_ids: Список ID использованных воспоминаний
            event_type: recalled, used, rejected, archived
            outcome: positive, neutral, negative, unknown (опционально)
            context: Дополнительный контекст (опционально)
        """
        for memory_id in memory_ids:
            event = MemoryEvent(
                memory_id=memory_id,
                user_id=user_id,
                event_type=event_type,
                outcome=outcome,
                context=context
            )
            db.add(event)
        
        await db.flush()
    
    async def increment_usage_count(
        self,
        db: AsyncSession,
        memory_ids: List[UUID]
    ):
        """
        Увеличить счётчик использования для воспоминаний.
        
        Args:
            db: Database session
            memory_ids: Список ID воспоминаний
        """
        stmt = (
            update(MemoryItem)
            .where(MemoryItem.id.in_(memory_ids))
            .values(usage_count=MemoryItem.usage_count + 1)
        )
        
        await db.execute(stmt)
        await db.flush()
    
    async def record_outcome(
        self,
        db: AsyncSession,
        memory_ids: List[UUID],
        outcome: str  # positive, negative, neutral
    ):
        """
        Записать исход использования памяти.
        
        Обновляет positive_outcomes или negative_outcomes в зависимости от outcome.
        
        Args:
            db: Database session
            memory_ids: Список ID воспоминаний
            outcome: positive, negative, neutral
        """
        if outcome == "positive":
            field = MemoryItem.positive_outcomes
        elif outcome == "negative":
            field = MemoryItem.negative_outcomes
        else:
            # neutral не учитывается
            return
        
        stmt = (
            update(MemoryItem)
            .where(MemoryItem.id.in_(memory_ids))
            .values({field.key: field + 1})
        )
        
        await db.execute(stmt)
        await db.flush()


# Global instance
memory_event_tracker = MemoryEventTracker()
