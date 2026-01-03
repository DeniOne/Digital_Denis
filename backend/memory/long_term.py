"""
Digital Den — Long-term Memory
═══════════════════════════════════════════════════════════════════════════

PostgreSQL-based long-term memory operations.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import MemoryItem, Topic, MemoryTopic
from core.encryption import encryptor


class LongTermMemory:
    """
    Long-term memory operations with PostgreSQL.
    """
    
    async def save(
        self,
        db: AsyncSession,
        item_type: str,
        content: str,
        summary: Optional[str] = None,
        structured_data: Optional[dict] = None,
        source_agent: Optional[str] = None,
        source_session: Optional[UUID] = None,
        confidence: float = 0.5,
        user_id: Optional[UUID] = None,
    ) -> MemoryItem:
        """Save new memory item."""
        # Encrypt sensitive fields
        encrypted_content = encryptor.encrypt(content)
        encrypted_summary = encryptor.encrypt(summary) if summary else None
        
        item = MemoryItem(
            user_id=user_id,
            item_type=item_type,
            content=encrypted_content,
            summary=encrypted_summary,
            structured_data=structured_data,
            source_agent=source_agent,
            source_session=source_session,
            confidence=confidence,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item
    
    def _decrypt_item(self, item: MemoryItem) -> MemoryItem:
        """Decrypt item content and summary."""
        if item:
            item.content = encryptor.decrypt(item.content)
            if item.summary:
                item.summary = encryptor.decrypt(item.summary)
        return item

    async def get(self, db: AsyncSession, item_id: UUID) -> Optional[MemoryItem]:
        """Get memory item by ID."""
        result = await db.execute(
            select(MemoryItem).where(MemoryItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        return self._decrypt_item(item) if item else None
    
    async def list(
        self,
        db: AsyncSession,
        user_id: Optional[UUID] = None,
        item_type: Optional[str] = None,
        status: str = "active",
        limit: int = 20,
        offset: int = 0,
    ) -> List[MemoryItem]:
        """List memory items with filters."""
        query = select(MemoryItem).where(MemoryItem.status == status)
        
        if user_id:
            query = query.where(MemoryItem.user_id == user_id)
        if item_type and item_type != "all":
            query = query.where(MemoryItem.item_type == item_type)
        
        query = query.order_by(desc(MemoryItem.created_at))
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        items = list(result.scalars().all())
        return [self._decrypt_item(item) for item in items]
    
    async def search(
        self,
        db: AsyncSession,
        query_text: str,
        user_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """Simple text search in memory items."""
        # Basic LIKE search (will be replaced with FTS or vector search)
        query = select(MemoryItem).where(
            and_(
                MemoryItem.status == "active",
                MemoryItem.content.ilike(f"%{query_text}%")
            )
        )
        
        if user_id:
            query = query.where(MemoryItem.user_id == user_id)
        
        query = query.order_by(desc(MemoryItem.created_at)).limit(limit)
        
        result = await db.execute(query)
        items = list(result.scalars().all())
        return [self._decrypt_item(item) for item in items]
    
    async def archive(self, db: AsyncSession, item_id: UUID) -> bool:
        """Archive memory item."""
        item = await self.get(db, item_id)
        if item:
            item.status = "archived"
            await db.commit()
            return True
        return False
    
    async def delete(self, db: AsyncSession, item_id: UUID) -> bool:
        """Soft delete memory item."""
        item = await self.get(db, item_id)
        if item:
            item.status = "deleted"
            await db.commit()
            return True
        return False
    
    async def get_context_memories(
        self,
        db: AsyncSession,
        topic_ids: Optional[List[UUID]] = None,
        limit: int = 5,
    ) -> List[MemoryItem]:
        """Get recent memories for context, optionally filtered by topics."""
        query = select(MemoryItem).where(
            MemoryItem.status == "active"
        ).order_by(desc(MemoryItem.accessed_at)).limit(limit)
        
        result = await db.execute(query)
        items = list(result.scalars().all())
        return [self._decrypt_item(item) for item in items]


# Global instance
long_term_memory = LongTermMemory()
