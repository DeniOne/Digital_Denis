# 🔍 TASK 10.1 — Vector DB Integration

**Проект:** Digital Denis v0.2.0  
**Статус:** ✅ Завершено  
**Приоритет:** Высокий  
**Оценка:** 3-4 дня  
**Зависимости:** Backend, PostgreSQL + PGVector

---

## 🎯 Цель

Усилить семантический поиск: оптимизация индексов, batch embedding, улучшение recall.

---

## 📋 Чеклист реализации

### PGVector Optimization
- [x] Создать HNSW индекс для embeddings
- [x] Настроить параметры индекса (m, ef_construction)
- [x] Benchmark: сравнить IVFFlat vs HNSW
- [x] Миграция для создания индексов

### Embedding Pipeline
- [x] Batch embedding для новых memories
- [x] Background job для индексации
- [x] Retry logic при ошибках API
- [x] Progress tracking для bulk operations

### Search API Enhancement
- [x] Hybrid search (vector + keyword)
- [x] Configurable similarity threshold
- [x] Result reranking
- [x] Filters (by type, date range, topics)

### Performance
- [x] Connection pooling для embedding API
- [x] Caching embeddings для частых queries
- [x] Latency < 100ms на 10k memories
- [x] Monitoring search performance

### Data Migration
- [x] Script для re-indexing существующих memories
- [x] Валидация качества embeddings
- [x] Cleanup orphaned embeddings

---

## 📦 Артефакты

```
backend/
├── memory/
│   ├── semantic.py             # ✅ Усилить
│   ├── embeddings.py           # Embedding generation
│   └── search.py               # Hybrid search
├── db/
│   └── migrations/
│       └── xxxx_optimize_vectors.py
└── scripts/
    └── reindex_memories.py     # Bulk reindex script
```

---

## 📝 Пример HNSW Index Migration

```python
# migrations/xxxx_optimize_vectors.py
"""Optimize vector indexes for better search performance."""

from alembic import op

def upgrade():
    # Drop existing index if any
    op.execute("""
        DROP INDEX IF EXISTS idx_memory_embeddings_embedding;
    """)
    
    # Create HNSW index (better for recall and speed)
    op.execute("""
        CREATE INDEX idx_memory_embeddings_hnsw 
        ON memory_embeddings 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)
    
    # Analyze table for query planner
    op.execute("ANALYZE memory_embeddings;")

def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_memory_embeddings_hnsw;")
```

---

## 📝 Пример Hybrid Search

```python
# memory/search.py
from sqlalchemy import text

async def hybrid_search(
    db: AsyncSession,
    query: str,
    user_id: UUID,
    limit: int = 10,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3,
):
    """
    Combine vector similarity with keyword matching.
    """
    # Get query embedding
    embedding = await get_embedding(query)
    
    sql = text("""
        WITH vector_results AS (
            SELECT 
                mi.id,
                1 - (me.embedding <=> :embedding::vector) as vector_score
            FROM memory_items mi
            JOIN memory_embeddings me ON mi.id = me.memory_id
            WHERE mi.user_id = :user_id AND mi.status = 'active'
            ORDER BY me.embedding <=> :embedding::vector
            LIMIT :limit * 2
        ),
        keyword_results AS (
            SELECT 
                id,
                ts_rank(to_tsvector('russian', content), query) as keyword_score
            FROM memory_items, plainto_tsquery('russian', :query) query
            WHERE user_id = :user_id AND status = 'active'
              AND to_tsvector('russian', content) @@ query
            LIMIT :limit * 2
        )
        SELECT 
            COALESCE(v.id, k.id) as id,
            COALESCE(v.vector_score, 0) * :vector_weight +
            COALESCE(k.keyword_score, 0) * :keyword_weight as combined_score
        FROM vector_results v
        FULL OUTER JOIN keyword_results k ON v.id = k.id
        ORDER BY combined_score DESC
        LIMIT :limit
    """)
    
    result = await db.execute(sql, {
        "embedding": str(embedding),
        "query": query,
        "user_id": user_id,
        "limit": limit,
        "vector_weight": vector_weight,
        "keyword_weight": keyword_weight,
    })
    
    return result.fetchall()
```

---

## 📊 Performance Targets

| Metric | Target | Acceptable |
|--------|--------|------------|
| Search latency (10k items) | <100ms | <200ms |
| Indexing throughput | 100 items/sec | 50 items/sec |
| Recall@10 | >0.85 | >0.75 |
| Memory usage | <2GB | <4GB |

---

## ✅ Критерии завершения

- [x] HNSW индекс создан и работает
- [x] Hybrid search возвращает релевантные результаты
- [x] Latency < 100ms на 10k memories
- [x] Все существующие memories переиндексированы

---

## 📎 Связанные документы

- [TASK 10.2 — Topic Auto-Clustering](./TASK_10.2_Topic_Clustering.md)
- [TASK 10.3 — Analytics Dashboard](./TASK_10.3_Analytics_Dashboard.md)
