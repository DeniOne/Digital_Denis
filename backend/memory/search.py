"""
Digital Denis — Search Service
═══════════════════════════════════════════════════════════════════════════

Implements advanced search capabilities:
- Vector Semantic Search (PGVector)
- Full Text Search (PostgreSQL tsvector)
- Hybrid Search (Combined ranking)
"""

from typing import List, Tuple, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import MemoryItem
from llm.openrouter import openrouter

class SearchService:
    """
    Handles memory retrieval using hybrid search techniques.
    """

    async def hybrid_search(
        self,
        db: AsyncSession,
        query: str,
        user_id: Optional[UUID] = None,
        limit: int = 10,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        similarity_threshold: float = 0.6
    ) -> List[Tuple[MemoryItem, float]]:
        """
        Search memories using both vector similarity and keyword matching.
        """
        # 1. Get query embedding
        try:
            query_embedding = await openrouter.get_embedding(query)
        except Exception:
            # Fallback to keyword-only search if embedding fails
            return await self.keyword_search(db, query, user_id, limit)

        # 2. Execute hybrid SQL query
        # We use Reciprocal Rank Fusion (RRF) or weighted sum. 
        # Here we use weighted sum of normalized scores.
        sql = text("""
            WITH vector_scores AS (
                SELECT 
                    mi.id,
                    1 - (me.embedding <=> :embedding::vector) as v_score
                FROM memory_items mi
                JOIN memory_embeddings me ON mi.id = me.memory_id
                WHERE mi.status = 'active'
                  AND (:user_id IS NULL OR mi.user_id = :user_id)
                ORDER BY me.embedding <=> :embedding::vector
                LIMIT :search_limit
            ),
            keyword_scores AS (
                SELECT 
                    id,
                    ts_rank_cd(to_tsvector('russian', content || ' ' || COALESCE(summary, '')), plainto_tsquery('russian', :query)) as k_score
                FROM memory_items
                WHERE status = 'active'
                  AND (:user_id IS NULL OR user_id = :user_id)
                  AND to_tsvector('russian', content || ' ' || COALESCE(summary, '')) @@ plainto_tsquery('russian', :query)
                LIMIT :search_limit
            )
            SELECT 
                mi.*,
                COALESCE(v.v_score, 0) * :v_weight + COALESCE(k.k_score, 0) * :k_weight as combined_score
            FROM memory_items mi
            LEFT JOIN vector_scores v ON mi.id = v.id
            LEFT JOIN keyword_scores k ON mi.id = k.id
            WHERE (v.id IS NOT NULL OR k.id IS NOT NULL)
              AND (COALESCE(v.v_score, 0) >= :threshold OR k.id IS NOT NULL)
            ORDER BY combined_score DESC
            LIMIT :limit
        """)

        result = await db.execute(sql, {
            "embedding": str(query_embedding),
            "query": query,
            "user_id": user_id,
            "limit": limit,
            "search_limit": limit * 3,
            "v_weight": vector_weight,
            "k_weight": keyword_weight,
            "threshold": similarity_threshold
        })

        rows = result.fetchall()
        
        results = []
        for row in rows:
            # Construct MemoryItem from RowProxy-like object
            item = MemoryItem(
                id=row.id,
                user_id=row.user_id,
                item_type=row.item_type,
                content=row.content,
                summary=row.summary,
                structured_data=row.structured_data,
                source_agent=row.source_agent,
                confidence=row.confidence,
                status=row.status,
                created_at=row.created_at
            )
            results.append((item, float(row.combined_score)))
            
        return results

    async def keyword_search(
        self,
        db: AsyncSession,
        query: str,
        user_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[Tuple[MemoryItem, float]]:
        """Fallback keyword-only search."""
        sql = text("""
            SELECT *, ts_rank_cd(to_tsvector('russian', content), plainto_tsquery('russian', :query)) as score
            FROM memory_items
            WHERE status = 'active'
              AND (:user_id IS NULL OR user_id = :user_id)
              AND to_tsvector('russian', content) @@ plainto_tsquery('russian', :query)
            ORDER BY score DESC
            LIMIT :limit
        """)
        result = await db.execute(sql, {"query": query, "user_id": user_id, "limit": limit})
        rows = result.fetchall()
        
        return [(MemoryItem(id=row.id, content=row.content), float(row.score)) for row in rows]

search_service = SearchService()
