# 💾 TASK 2.1 — Memory Layer Design

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Высокий  
**Зависимости:** TASK 1.3

---

## 📋 Чеклист реализации

- [x] Создать backend/memory/models.py (SQLAlchemy)
- [x] Создать backend/memory/short_term.py (Redis)
- [x] Создать backend/memory/long_term.py (PostgreSQL)
- [ ] Создать backend/memory/semantic.py (Vector DB) — v0.2
- [ ] Миграции Alembic готовы
- [x] CRUD операции работают
- [ ] Написать unit-тесты

---

## 🎯 Цель

Спроектировать Memory Layer: short/long/semantic память, схемы БД, жизненный цикл.

---

## 📦 Артефакты

### 1. Архитектура Memory Layer

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MEMORY LAYER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────┐      │
│  │                    SHORT-TERM MEMORY                          │      │
│  │                         (Redis)                               │      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │      │
│  │  │   Session   │  │    Chat     │  │   Working   │           │      │
│  │  │   Context   │  │   History   │  │   Buffer    │           │      │
│  │  │   TTL: 1h   │  │   TTL: 24h  │  │   TTL: 5m   │           │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘           │      │
│  └───────────────────────────────────────────────────────────────┘      │
│                                    │                                     │
│                                    ▼ (promote)                           │
│  ┌───────────────────────────────────────────────────────────────┐      │
│  │                    LONG-TERM MEMORY                           │      │
│  │                      (PostgreSQL)                             │      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │      │
│  │  │  Decisions  │  │   Insights  │  │    Facts    │           │      │
│  │  │             │  │             │  │             │           │      │
│  │  │ Structured  │  │ Semi-struct │  │   Atomic    │           │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘           │      │
│  └───────────────────────────────────────────────────────────────┘      │
│                                    │                                     │
│                                    ▼ (index)                             │
│  ┌───────────────────────────────────────────────────────────────┐      │
│  │                    SEMANTIC MEMORY                            │      │
│  │                    (FAISS/Weaviate)                           │      │
│  │  ┌─────────────────────────────────────────────────────┐     │      │
│  │  │              Vector Embeddings                       │     │      │
│  │  │  • Semantic similarity search                        │     │      │
│  │  │  • Contextual retrieval                              │     │      │
│  │  └─────────────────────────────────────────────────────┘     │      │
│  └───────────────────────────────────────────────────────────────┘      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 2. DB Schema — Short-term Memory (Redis)

```python
# Redis Key Patterns

# Session context (current state)
session:{user_id}:{session_id} = {
    "started_at": "2024-01-15T10:30:00Z",
    "last_activity": "2024-01-15T10:45:00Z",
    "active_topics": ["finances", "hr"],
    "current_mode": "strategic",
    "metadata": {}
}
# TTL: 1 hour

# Chat history (last N messages)
chat:{user_id}:{session_id} = [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "timestamp": "..."},
    ...
]
# TTL: 24 hours
# Max length: 50 messages

# Working buffer (temporary processing)
buffer:{user_id}:{request_id} = {
    "input": "...",
    "context": {...},
    "agent": "core",
    "status": "processing"
}
# TTL: 5 minutes
```

---

### 3. DB Schema — Long-term Memory (PostgreSQL)

```sql
-- Core memory items table
CREATE TABLE memory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    
    -- Type classification
    item_type VARCHAR(50) NOT NULL,  -- decision, insight, fact, thought
    
    -- Content
    content TEXT NOT NULL,
    summary TEXT,  -- LLM-generated summary
    
    -- Structured data (for decisions)
    structured_data JSONB,  -- hypothesis, arguments, etc.
    
    -- Metadata
    source_agent VARCHAR(50),  -- which agent created
    source_session UUID,
    confidence FLOAT DEFAULT 0.5,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- active, archived, aggregated, deleted
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Topics table
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES topics(id),
    level INTEGER DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Memory-Topic links
CREATE TABLE memory_topics (
    memory_id UUID REFERENCES memory_items(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (memory_id, topic_id)
);

-- Memory relationships (for graphs)
CREATE TABLE memory_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES memory_items(id) ON DELETE CASCADE,
    target_id UUID REFERENCES memory_items(id) ON DELETE CASCADE,
    relation_type VARCHAR(50),  -- depends_on, contradicts, evolves_from, reinforces
    confidence FLOAT DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Aggregations (compressed memory)
CREATE TABLE memory_aggregations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    aggregation_type VARCHAR(50),  -- daily, weekly, topic_based
    content TEXT NOT NULL,
    source_ids UUID[],  -- original items
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_memory_items_user ON memory_items(user_id);
CREATE INDEX idx_memory_items_type ON memory_items(item_type);
CREATE INDEX idx_memory_items_status ON memory_items(status);
CREATE INDEX idx_memory_items_created ON memory_items(created_at DESC);
CREATE INDEX idx_memory_topics_topic ON memory_topics(topic_id);
```

---

### 4. Semantic Memory (Vector DB)

```python
# FAISS / Weaviate Configuration

# Collection schema
memory_vectors = {
    "name": "memory_embeddings",
    "vectorizer": "text2vec-openai",  # or sentence-transformers
    "vector_dimensions": 1536,  # OpenAI ada-002
    
    "properties": [
        {"name": "memory_id", "dataType": ["uuid"]},
        {"name": "content", "dataType": ["text"]},
        {"name": "item_type", "dataType": ["string"]},
        {"name": "created_at", "dataType": ["date"]},
    ]
}

# Indexing strategy
class SemanticMemory:
    async def index(self, memory_item: MemoryItem) -> str:
        """Index memory item with embedding"""
        embedding = await self.embed(memory_item.content)
        return await self.vector_db.insert(
            vector=embedding,
            metadata={
                "memory_id": str(memory_item.id),
                "item_type": memory_item.item_type,
                "content": memory_item.content[:500],  # truncated for search
            }
        )
    
    async def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """Semantic similarity search"""
        query_embedding = await self.embed(query)
        results = await self.vector_db.search(
            vector=query_embedding,
            limit=limit,
            filter={"status": "active"}
        )
        return [await self.get_full_item(r.memory_id) for r in results]
```

---

### 5. Memory Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       MEMORY ITEM LIFECYCLE                             │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────┐
    │ CREATE  │ ◀─── Agent detects decision/insight/fact
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │ ACTIVE  │ ◀─── searchable, contributes to context
    └────┬────┘
         │
         ├─────────────────────────────────────────┐
         │                                         │
         ▼                                         ▼
    ┌─────────┐                              ┌───────────┐
    │AGGREGATE│ ◀─── similar items merged    │  ARCHIVE  │ ◀─── old, low access
    └────┬────┘                              └─────┬─────┘
         │                                         │
         │      ┌─────────────────────────────────┘
         │      │
         ▼      ▼
    ┌─────────────┐
    │   FORGET    │ ◀─── explicit user request + confirmation
    └─────────────┘
```

| Стадия | Триггер | Действие | Reversible |
|--------|---------|----------|------------|
| **Create** | Agent.process() | Insert into PostgreSQL + Vector DB | N/A |
| **Active** | Default state | Fully searchable, included in context | N/A |
| **Aggregate** | Similar items > threshold | Merge into summary, archive originals | ✅ |
| **Archive** | Age > 90 days, low access | Exclude from default search | ✅ |
| **Forget** | User request + confirm | Soft delete (status = deleted) | ✅ (30 days) |

---

### 6. Memory Operations API

```python
class MemoryService:
    async def save(self, item: MemoryItemCreate) -> MemoryItem:
        """Save new memory item"""
        # 1. Insert into PostgreSQL
        db_item = await self.db.insert(item)
        # 2. Index in Vector DB
        await self.semantic.index(db_item)
        # 3. Extract topics (async)
        await self.queue.enqueue("extract_topics", db_item.id)
        return db_item
    
    async def search(
        self, 
        query: str, 
        limit: int = 5,
        item_types: List[str] = None,
        topic_ids: List[UUID] = None,
        date_range: DateRange = None
    ) -> List[MemoryItem]:
        """Combined keyword + semantic search"""
        # Semantic search
        semantic_results = await self.semantic.search(query, limit=limit*2)
        # Filter by criteria
        filtered = self.filter(semantic_results, item_types, topic_ids, date_range)
        return filtered[:limit]
    
    async def get_context_memories(
        self, 
        session_id: UUID, 
        current_message: str
    ) -> List[MemoryItem]:
        """Get memories relevant to current context"""
        # 1. Get active topic from session
        session = await self.redis.get_session(session_id)
        # 2. Semantic search by message
        semantic = await self.search(current_message, limit=3)
        # 3. Recent by topic
        by_topic = await self.get_by_topics(session.active_topics, limit=2)
        # 4. Deduplicate and rank
        return self.rank_and_dedupe(semantic + by_topic)
```

---

## ✅ Критерии завершения

- [x] Все 3 типа памяти описаны
- [x] Схемы БД готовы к реализации
- [x] Жизненный цикл формализован
- [x] Интеграция с Memory Agent понятна

---

## 📎 Связанные документы

- [TASK 1.3 — Agent Specification](../phase-1/TASK_1.3_Agent_Specification.md)
- [TASK 2.2 — Topic Intelligence](./TASK_2.2_Topic_Intelligence.md)
- [TASK 2.3 — Memory Agent Spec](./TASK_2.3_Memory_Agent_Spec.md)
