"""
Digital Den — RAG 2.0 Search Service
═══════════════════════════════════════════════════════════════════════════

Intent-aware hybrid search with time decay and conflict detection.
"""

from typing import List, Tuple, Optional, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import MemoryItem, ConversationState
from memory.ranking_config import (
    get_memory_weight,
    calculate_time_decay,
    INTENT_BASE_WEIGHT
)
from llm.openrouter import openrouter
from core.encryption import encryptor


class RAG2SearchService:
    """
    RAG 2.0 Hybrid Search with intent-aware ranking, time decay, and Kaizen boost.
    """
    
    async def hybrid_search(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID,
        intent: str = "casual",
        conversation_state: Optional[ConversationState] = None,
        limit: int = 10,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        similarity_threshold: float = 0.5
    ) -> List[Tuple[MemoryItem, float]]:
        """
        RAG 2.0 intent-aware hybrid search.
        
        Args:
            db: Database session
            query: Search query
            user_id: User ID
            intent: User intent (decision_request, analysis, etc.)
            conversation_state: Current conversation state (для query expansion)
            limit: Maximum results
            vector_weight: Weight for semantic similarity
            keyword_weight: Weight for keyword matching
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of (MemoryItem, final_score) sorted by relevance
        """
        # 1. Query expansion через active_entities из conversation_state
        expanded_query = query
        if conversation_state and conversation_state.active_entities:
            # Добавляем активные сущности к запросу
            entities_str = " ".join(conversation_state.active_entities[:3])  # топ-3
            expanded_query = f"{query} {entities_str}"
        
        # 2. Получение embedding
        try:
            query_embedding = await openrouter.get_embedding(expanded_query)
        except Exception as e:
            print(f"Embedding error: {e}, falling back to keyword search")
            return await self._keyword_search_fallback(db, query, user_id, limit)
        
        # 3. Векторный поиск с метаданными
        results = await self._execute_vector_search(
            db, query_embedding, query, user_id, limit * 3, vector_weight, keyword_weight, similarity_threshold
        )
        
        # 4. Применение RAG 2.0 ранжирования
        scored_results = []
        now = datetime.utcnow()
        
        for item, semantic_score in results:
            # Memory type weight
            memory_type_weight = get_memory_weight(item.item_type, intent)
            
            # Intent weight (базовый)
            intent_weight = INTENT_BASE_WEIGHT
            
            # Time decay
            time_decay = calculate_time_decay(item.item_type, item.created_at, now)
            
            # Kaizen boost (эффективность памяти)
            kaizen_boost = 1.0
            if item.usage_count > 0:
                total_outcomes = item.positive_outcomes + item.negative_outcomes
                if total_outcomes > 0:
                    effectiveness = (item.positive_outcomes - item.negative_outcomes) / total_outcomes
                    kaizen_boost = 1.0 + (effectiveness * 0.15)  # макс +15% за высокую эффективность
            
            # Финальный скор
            final_score = (
                semantic_score
                * memory_type_weight
                * intent_weight
                * time_decay
                * kaizen_boost
            )
            
            scored_results.append((item, final_score))
        
        # 5. Сортировка и возврат топ-N
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:limit]
    
    async def _execute_vector_search(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        query_text: str,
        user_id: UUID,
        search_limit: int,
        vector_weight: float,
        keyword_weight: float,
        similarity_threshold: float
    ) -> List[Tuple[MemoryItem, float]]:
        """
        Внутренний метод: выполняет гибридный поиск (semantic + FTS).
        
        Returns:
            List of (MemoryItem, semantic_score)
        """
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        user_filter = "mi.user_id = cast(:user_id as uuid)"
        user_filter_simple = "user_id = cast(:user_id as uuid)"
        
        sql = text(f"""
            WITH vector_scores AS (
                SELECT 
                    mi.id,
                    mi.user_id,
                    mi.item_type,
                    mi.content,
                    mi.summary,
                    mi.structured_data,
                    mi.source_agent,
                    mi.confidence,
                    mi.related_to,
                    mi.usage_count,
                    mi.positive_outcomes,
                    mi.negative_outcomes,
                    mi.confidence_level,
                    mi.status,
                    mi.created_at,
                    mi.updated_at,
                    1 - cosine_distance(me.embedding, cast(:embedding as vector)) as v_score
                FROM memory_items mi
                JOIN memory_embeddings me ON mi.id = me.memory_id
                WHERE mi.status = 'active'
                  AND {user_filter}
                ORDER BY cosine_distance(me.embedding, cast(:embedding as vector))
                LIMIT :search_limit
            ),
            keyword_scores AS (
                SELECT 
                    id,
                    ts_rank_cd(to_tsvector('russian', content || ' ' || COALESCE(summary, '')), plainto_tsquery('russian', :query)) as k_score
                FROM memory_items
                WHERE status = 'active'
                  AND {user_filter_simple}
                  AND to_tsvector('russian', content || ' ' || COALESCE(summary, '')) @@ plainto_tsquery('russian', :query)
                LIMIT :search_limit
            )
            SELECT 
                vs.*,
                COALESCE(vs.v_score, 0) * :v_weight + COALESCE(k.k_score, 0) * :k_weight as combined_score
            FROM vector_scores vs
            LEFT JOIN keyword_scores k ON vs.id = k.id
            WHERE (vs.v_score >= :threshold OR k.id IS NOT NULL)
            ORDER BY combined_score DESC
            LIMIT :search_limit
        """)
        
        params = {
            "embedding": embedding_str,
            "query": query_text,
            "user_id": str(user_id),
            "search_limit": search_limit,
            "v_weight": vector_weight,
            "k_weight": keyword_weight,
            "threshold": similarity_threshold
        }
        
        result = await db.execute(sql, params)
        rows = result.fetchall()
        
        results = []
        for row in rows:
            # Расшифровываем контент перед использованием
            decrypted_content = encryptor.decrypt(row.content) if row.content else row.content
            decrypted_summary = encryptor.decrypt(row.summary) if row.summary else row.summary
            
            item = MemoryItem(
                id=row.id,
                user_id=row.user_id,
                item_type=row.item_type,
                content=decrypted_content,
                summary=decrypted_summary,
                structured_data=row.structured_data,
                source_agent=row.source_agent,
                confidence=row.confidence,
                related_to=row.related_to,
                usage_count=row.usage_count,
                positive_outcomes=row.positive_outcomes,
                negative_outcomes=row.negative_outcomes,
                confidence_level=row.confidence_level,
                status=row.status,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            results.append((item, float(row.combined_score)))
        
        return results
    
    async def _keyword_search_fallback(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID,
        limit: int
    ) -> List[Tuple[MemoryItem, float]]:
        """Fallback: keyword-only search если embedding не работает"""
        sql = text("""
            SELECT *, ts_rank_cd(to_tsvector('russian', content), plainto_tsquery('russian', :query)) as score
            FROM memory_items
            WHERE status = 'active'
              AND user_id = cast(:user_id as uuid)
              AND to_tsvector('russian', content) @@ plainto_tsquery('russian', :query)
            ORDER BY score DESC
            LIMIT :limit
        """)
        result = await db.execute(sql, {"query": query, "user_id": str(user_id), "limit": limit})
        rows = result.fetchall()
        
        results = []
        for row in rows:
            decrypted_content = encryptor.decrypt(row.content) if row.content else row.content
            item = MemoryItem(id=row.id, content=decrypted_content, item_type=row.item_type, created_at=row.created_at, usage_count=0, positive_outcomes=0, negative_outcomes=0)
            results.append((item, float(row.score)))
        
        return results


# ═══════════════════════════════════════════════════════════════════════════
# Conflict Detection
# ═══════════════════════════════════════════════════════════════════════════

def detect_conflicts(memories: List[MemoryItem]) -> List[Dict]:
    """
    Обнаруживает противоречия между воспоминаниями.
    
    Простая эвристика: ищет пары (decision, hypothesis) на похожие темы.
    
    Returns:
        Список конфликтов вида:
        [
            {
                "memory_a": MemoryItem,
                "memory_b": MemoryItem,
                "type": "decision_vs_hypothesis",
                "confidence": 0.8
            }
        ]
    """
    conflicts = []
    
    # Простой подход: проверяем противоречия по типам
    decisions = [m for m in memories if m.item_type == "decision"]
    hypotheses = [m for m in memories if m.item_type == "hypothesis"]
    
    for decision in decisions:
        for hypothesis in hypotheses:
            # Упрощённая проверка: если оба содержат общие ключевые слова, но разные выводы
            # (В production можно использовать semantic similarity между embeddings)
            decision_words = set(decision.content.lower().split())
            hypothesis_words = set(hypothesis.content.lower().split())
            
            common_words = decision_words & hypothesis_words
            
            # Если есть 3+ общих слова — возможен конфликт
            if len(common_words) >= 3:
                conflicts.append({
                    "memory_a": decision,
                    "memory_b": hypothesis,
                    "type": "decision_vs_hypothesis",
                    "confidence": 0.7
                })
    
    return conflicts


# Global instance
rag2_search_service = RAG2SearchService()
