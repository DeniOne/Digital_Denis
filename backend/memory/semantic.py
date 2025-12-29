"""
Digital Denis — Semantic Memory Service
═══════════════════════════════════════════════════════════════════════════

Vector-based semantic search using PGVector.
"""

from typing import List, Optional, Tuple
from uuid import UUID
import asyncio

from sqlalchemy import Column, Text, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from pgvector.sqlalchemy import Vector

from memory.models import MemoryItem, Base
from llm.openrouter import openrouter


# ═══════════════════════════════════════════════════════════════════════════
# Vector Embedding Dimension
# ═══════════════════════════════════════════════════════════════════════════

EMBEDDING_DIMENSION = 1536  # OpenAI ada-002 / OpenRouter embeddings


# ═══════════════════════════════════════════════════════════════════════════
# Memory Embedding Model (extends MemoryItem)
# ═══════════════════════════════════════════════════════════════════════════

class MemoryEmbedding(Base):
    """
    Stores vector embeddings for memory items.
    Separate table to keep main table clean.
    """
    __tablename__ = "memory_embeddings"
    
    memory_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    embedding = Column(Vector(EMBEDDING_DIMENSION), nullable=False)
    model = Column(Text, default="text-embedding-ada-002")


# ═══════════════════════════════════════════════════════════════════════════
# Semantic Memory Service
# ═══════════════════════════════════════════════════════════════════════════

class SemanticMemoryService:
    """
    Service for semantic search and embedding management.
    
    Uses PGVector for vector storage and similarity search.
    Uses OpenRouter/OpenAI for generating embeddings.
    """
    
    def __init__(self):
        self.embedding_model = "openai/text-embedding-ada-002"
        self.dimension = EMBEDDING_DIMENSION
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using LLM provider.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Use OpenRouter's embedding endpoint
            embedding = await openrouter.get_embedding(text)
            return embedding
        except Exception as e:
            # Fallback: use a simple hash-based pseudo-embedding for dev
            # This is NOT for production - just for testing without API
            import hashlib
            hash_bytes = hashlib.sha256(text.encode()).digest()
            # Pad to embedding dimension
            pseudo_embedding = []
            for i in range(self.dimension):
                byte_idx = i % len(hash_bytes)
                pseudo_embedding.append(float(hash_bytes[byte_idx]) / 255.0)
            return pseudo_embedding
    
    async def index(
        self, 
        db: AsyncSession, 
        memory_id: UUID, 
        text: str
    ) -> bool:
        """
        Index a memory item by generating and storing its embedding.
        
        Args:
            db: Database session
            memory_id: UUID of the memory item
            text: Text content to embed
            
        Returns:
            True if indexing successful
        """
        try:
            # Generate embedding
            embedding = await self.get_embedding(text)
            
            # Check if embedding already exists
            result = await db.execute(
                select(MemoryEmbedding).where(MemoryEmbedding.memory_id == memory_id)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing embedding
                existing.embedding = embedding
            else:
                # Create new embedding
                mem_embedding = MemoryEmbedding(
                    memory_id=memory_id,
                    embedding=embedding,
                    model=self.embedding_model,
                )
                db.add(mem_embedding)
            
            await db.commit()
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"Error indexing memory {memory_id}: {e}")
            return False
    
    async def search(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Tuple[MemoryItem, float]]:
        """
        Semantic search for memories similar to query.
        
        Args:
            db: Database session
            query: Search query text
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of (MemoryItem, similarity_score) tuples
        """
        try:
            # Generate query embedding
            query_embedding = await self.get_embedding(query)
            
            # Search using cosine similarity
            # PGVector uses <=> for cosine distance (lower = more similar)
            # We convert to similarity: 1 - distance
            sql = text("""
                SELECT 
                    mi.*,
                    1 - (me.embedding <=> :query_embedding::vector) as similarity
                FROM memory_items mi
                JOIN memory_embeddings me ON mi.id = me.memory_id
                WHERE mi.status = 'active'
                ORDER BY me.embedding <=> :query_embedding::vector
                LIMIT :limit
            """)
            
            result = await db.execute(
                sql,
                {
                    "query_embedding": str(query_embedding),
                    "limit": limit,
                }
            )
            
            rows = result.fetchall()
            
            # Filter by threshold and convert to MemoryItem objects
            results = []
            for row in rows:
                similarity = row.similarity
                if similarity >= similarity_threshold:
                    # Reconstruct MemoryItem from row
                    memory = MemoryItem(
                        id=row.id,
                        user_id=row.user_id,
                        item_type=row.item_type,
                        content=row.content,
                        summary=row.summary,
                        confidence=row.confidence,
                        created_at=row.created_at,
                    )
                    results.append((memory, similarity))
            
            return results
            
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []
    
    async def find_similar(
        self,
        db: AsyncSession,
        memory_id: UUID,
        limit: int = 5,
    ) -> List[Tuple[MemoryItem, float]]:
        """
        Find memories similar to a specific memory item.
        
        Args:
            db: Database session
            memory_id: UUID of the reference memory
            limit: Maximum number of results
            
        Returns:
            List of (MemoryItem, similarity_score) tuples
        """
        try:
            # Get the embedding of the reference memory
            result = await db.execute(
                select(MemoryEmbedding).where(MemoryEmbedding.memory_id == memory_id)
            )
            ref_embedding = result.scalar_one_or_none()
            
            if not ref_embedding:
                return []
            
            # Search for similar (excluding self)
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
            
            result = await db.execute(
                sql,
                {
                    "ref_embedding": str(list(ref_embedding.embedding)),
                    "memory_id": memory_id,
                    "limit": limit,
                }
            )
            
            rows = result.fetchall()
            
            results = []
            for row in rows:
                memory = MemoryItem(
                    id=row.id,
                    user_id=row.user_id,
                    item_type=row.item_type,
                    content=row.content,
                    summary=row.summary,
                    confidence=row.confidence,
                    created_at=row.created_at,
                )
                results.append((memory, row.similarity))
            
            return results
            
        except Exception as e:
            print(f"Error finding similar memories: {e}")
            return []
    
    async def reindex_all(self, db: AsyncSession) -> int:
        """
        Reindex all memory items.
        Useful after model changes or for initial population.
        
        Returns:
            Number of items indexed
        """
        result = await db.execute(
            select(MemoryItem).where(MemoryItem.status == "active")
        )
        memories = result.scalars().all()
        
        indexed = 0
        for memory in memories:
            text_to_embed = f"{memory.content}"
            if memory.summary:
                text_to_embed += f"\n{memory.summary}"
            
            success = await self.index(db, memory.id, text_to_embed)
            if success:
                indexed += 1
        
        return indexed


# Global instance
semantic_memory = SemanticMemoryService()
