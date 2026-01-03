"""
Digital Den — Embedding Service
═══════════════════════════════════════════════════════════════════════════

Handles generation and storage of vector embeddings.
Supports batch processing and retry logic.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import MemoryItem, MemoryEmbedding
from llm.openrouter import openrouter

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating and managing embeddings for memory items.
    """
    
    def __init__(self, batch_size: int = 20):
        self.batch_size = batch_size
        self.model = "openai/text-embedding-ada-002"

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate a single embedding with retry."""
        for attempt in range(3):
            try:
                return await openrouter.get_embedding(text, model=self.model)
            except Exception as e:
                logger.warning(f"Embedding generation attempt {attempt+1} failed: {e}")
                if attempt == 2: raise
                await asyncio.sleep(1 * (attempt + 1))
        return []

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate multiple embeddings in one API call."""
        if not texts:
            return []
        try:
            return await openrouter.get_embeddings(texts, model=self.model)
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            # Fallback to individual if batch fails (could be too large)
            results = []
            for text in texts:
                results.append(await self.generate_embedding(text))
            return results

    async def index_items(self, db: AsyncSession, memory_ids: List[UUID]) -> int:
        """
        Index multiple memory items.
        """
        if not memory_ids:
            return 0
            
        # 1. Fetch memory items
        result = await db.execute(
            select(MemoryItem).where(MemoryItem.id.in_(memory_ids))
        )
        items = result.scalars().all()
        if not items:
            return 0
            
        # 2. Prepare texts for embedding
        # We combine content and summary for better semantic representation
        texts = []
        for item in items:
            text = item.content
            if item.summary:
                text += f"\n{item.summary}"
            texts.append(text)
            
        # 3. Generate embeddings
        embeddings = await self.generate_embeddings_batch(texts)
        
        # 4. Store in database
        indexed_count = 0
        for i, item in enumerate(items):
            if i >= len(embeddings): break
            
            # Upsert logic
            stmt = select(MemoryEmbedding).where(MemoryEmbedding.memory_id == item.id)
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()
            
            if existing:
                existing.embedding = embeddings[i]
                existing.model = self.model
            else:
                new_emb = MemoryEmbedding(
                    memory_id=item.id,
                    embedding=embeddings[i],
                    model=self.model
                )
                db.add(new_emb)
            indexed_count += 1
            
        await db.commit()
        return indexed_count

    async def cleanup_orphaned(self, db: AsyncSession) -> int:
        """Remove embeddings that don't have a corresponding memory item."""
        # This is handled by ON DELETE CASCADE, but useful for manual cleanup if needed
        stmt = delete(MemoryEmbedding).where(
            ~MemoryEmbedding.memory_id.in_(select(MemoryItem.id))
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

embedding_service = EmbeddingService()
