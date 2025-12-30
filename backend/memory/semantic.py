"""
Digital Denis — Semantic Memory Service
═══════════════════════════════════════════════════════════════════════════

Facade for semantic search and embedding management.
Integrates embeddings.py and search.py.
"""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import MemoryItem
from memory.embeddings import embedding_service
from memory.search import search_service


class SemanticMemoryService:
    """
    Facade service for semantic operations.
    Maintains backward compatibility with original SemanticMemoryService API.
    """
    
    def __init__(self):
        self.embedding_model = embedding_service.model
        self.dimension = 1536
    
    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        return await embedding_service.generate_embedding(text)
    
    async def index(
        self, 
        db: AsyncSession, 
        memory_id: UUID, 
        text: Optional[str] = None
    ) -> bool:
        """
        Index a memory item safely.
        """
        try:
            indexed = await embedding_service.index_items(db, [memory_id])
            return indexed > 0
        except Exception as e:
            print(f"Error indexing memory {memory_id}: {e}")
            return False
    
    async def search(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 5,
        user_id: Optional[UUID] = None,
        similarity_threshold: float = 0.6,
    ) -> List[Tuple[MemoryItem, float]]:
        """
        Hybrid semantic search for memories similar to query.
        """
        return await search_service.hybrid_search(
            db=db,
            query=query,
            user_id=user_id,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
    
    async def find_similar(
        self,
        db: AsyncSession,
        memory_id: UUID,
        limit: int = 5,
    ) -> List[Tuple[MemoryItem, float]]:
        """
        Find memories similar to a specific memory item.
        """
        # Get the embedding of the reference memory first
        from memory.models import MemoryEmbedding
        from sqlalchemy import select
        
        result = await db.execute(
            select(MemoryEmbedding).where(MemoryEmbedding.memory_id == memory_id)
        )
        ref_embedding = result.scalar_one_or_none()
        
        if not ref_embedding:
            return []
            
        # Re-use search logic but with direct vector comparison
        from sqlalchemy import text
        sql = text("""
            SELECT 
                mi.*,
                1 - (me.embedding <=> :ref_embedding::vector) as similarity
            FROM memory_items mi
            JOIN memory_embeddings me ON mi.id = me.memory_id
            WHERE mi.status = 'active'
              AND mi.id != :memory_id
            ORDER BY me.embedding <=> :ref_embedding::vector
            LIMIT :limit
        """)
        
        result = await db.execute(sql, {
            "ref_embedding": str(list(ref_embedding.embedding)),
            "memory_id": memory_id,
            "limit": limit
        })
        
        rows = result.fetchall()
        
        results = []
        for row in rows:
            item = MemoryItem(
                id=row.id,
                content=row.content,
                # Add other fields as needed
            )
            results.append((item, float(row.similarity)))
            
        return results
    
    async def reindex_all(self, db: AsyncSession) -> int:
        """Reindex all active memories."""
        from memory.models import MemoryItem
        from sqlalchemy import select
        
        result = await db.execute(
            select(MemoryItem.id).where(MemoryItem.status == 'active')
        )
        ids = [row[0] for row in result.fetchall()]
        
        # Batch index
        total_indexed = 0
        batch_size = 20
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            total_indexed += await embedding_service.index_items(db, batch_ids)
            
        return total_indexed


# Global instance for compatibility
semantic_memory = SemanticMemoryService()
