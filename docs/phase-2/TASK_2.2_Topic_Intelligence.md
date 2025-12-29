# 🏷️ TASK 2.2 — Topic Intelligence Engine

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Средний  
**Зависимости:** TASK 2.1

---

## 📋 Чеклист реализации (v0.2)

- [x] Создать таблицу topics в PostgreSQL
- [x] Создать backend/analytics/topics.py
- [x] Реализовать TopicExtractor с LLM
- [x] Загрузить дефолтную иерархию тем
- [x] Реализовать topic stats API
- [x] Написать unit-тесты

---

## 🎯 Цель

Спроектировать Topic Intelligence Engine: извлечение тем, иерархию, связь с memory items, confidence score.

---

## 📦 Артефакты

### 1. Архитектура Topic Intelligence

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      TOPIC INTELLIGENCE ENGINE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    TOPIC EXTRACTION                              │    │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │    │
│  │  │ Memory Item │ => │  LLM-lite   │ => │ Topic List  │          │    │
│  │  │   Content   │    │ Classifier  │    │ + Confidence│          │    │
│  │  └─────────────┘    └─────────────┘    └─────────────┘          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│                                    ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    HIERARCHY MANAGER                             │    │
│  │                                                                  │    │
│  │         [Strategy]                                               │    │
│  │             │                                                    │    │
│  │    ┌───────┼───────┐                                             │    │
│  │    ▼       ▼       ▼                                             │    │
│  │ [Finance] [HR] [Operations]                                      │    │
│  │    │       │       │                                             │    │
│  │    ├──[Budget]     ├──[Hiring]                                   │    │
│  │    ├──[Revenue]    ├──[Training]                                 │    │
│  │    └──[Costs]      └──[KPI]                                      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│                                    ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    TOPIC STATISTICS                              │    │
│  │  • Frequency tracking                                            │    │
│  │  • Trend analysis                                                │    │
│  │  • Activity heatmaps                                             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 2. Topic Data Model

```sql
-- Topics table (with hierarchy)
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Hierarchy
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    parent_id UUID REFERENCES topics(id),
    level INTEGER DEFAULT 0,  -- 0 = root
    path LTREE,  -- for efficient hierarchy queries
    
    -- Description
    description TEXT,
    keywords TEXT[],  -- associated keywords for matching
    
    -- Configuration
    is_system BOOLEAN DEFAULT FALSE,  -- system-created vs user-created
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Stats (denormalized for performance)
    item_count INTEGER DEFAULT 0,
    last_activity TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Memory-Topic associations
CREATE TABLE memory_topics (
    memory_id UUID REFERENCES memory_items(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    
    -- Classification confidence
    confidence FLOAT NOT NULL DEFAULT 0.5,
    
    -- Source
    assigned_by VARCHAR(50),  -- llm, user, rule
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (memory_id, topic_id)
);

-- Topic statistics (time-series)
CREATE TABLE topic_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    
    -- Time bucket
    period_start DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL,  -- daily, weekly, monthly
    
    -- Metrics
    item_count INTEGER DEFAULT 0,
    decision_count INTEGER DEFAULT 0,
    insight_count INTEGER DEFAULT 0,
    avg_confidence FLOAT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(topic_id, period_start, period_type)
);

-- Indexes
CREATE INDEX idx_topics_parent ON topics(parent_id);
CREATE INDEX idx_topics_path ON topics USING GIST(path);
CREATE INDEX idx_memory_topics_topic ON memory_topics(topic_id);
CREATE INDEX idx_topic_stats_period ON topic_stats(topic_id, period_start);
```

---

### 3. Default Topic Hierarchy

```yaml
# ai/config/topics.yaml
topics:
  - name: "Strategy"
    slug: "strategy"
    children:
      - name: "Vision"
        slug: "vision"
      - name: "Goals"
        slug: "goals"
      - name: "Planning"
        slug: "planning"
        
  - name: "Finance"
    slug: "finance"
    children:
      - name: "Budget"
        slug: "budget"
      - name: "Revenue"
        slug: "revenue"
      - name: "Costs"
        slug: "costs"
      - name: "Investments"
        slug: "investments"
        
  - name: "HR"
    slug: "hr"
    children:
      - name: "Hiring"
        slug: "hiring"
      - name: "Training"
        slug: "training"
      - name: "Motivation"
        slug: "motivation"
      - name: "KPI"
        slug: "kpi"
        
  - name: "Operations"
    slug: "operations"
    children:
      - name: "Processes"
        slug: "processes"
      - name: "Quality"
        slug: "quality"
      - name: "Efficiency"
        slug: "efficiency"
        
  - name: "Product"
    slug: "product"
    children:
      - name: "Development"
        slug: "development"
      - name: "Features"
        slug: "features"
        
  - name: "Marketing"
    slug: "marketing"
    children:
      - name: "Promotion"
        slug: "promotion"
      - name: "Brand"
        slug: "brand"
```

---

### 4. Topic Processing Pipeline

```
┌────────────────────────────────────────────────────────────────────────┐
│                    TOPIC EXTRACTION PIPELINE                           │
└────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐
│ Memory Item │ => │ Pre-process  │ => │ LLM Classify │ => │ Post-proc │
│   Created   │    │ (clean text) │    │ (multi-label)│    │ (validate)│
└─────────────┘    └──────────────┘    └──────────────┘    └─────┬─────┘
                                                                  │
                   ┌──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  RESULTS                                                                 │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ [                                                              │     │
│  │   {"topic": "finance/budget", "confidence": 0.85},            │     │
│  │   {"topic": "hr/kpi", "confidence": 0.72}                     │     │
│  │ ]                                                              │     │
│  └────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
```

**Pipeline implementation:**

```python
class TopicExtractor:
    def __init__(self, llm: LLMProvider, topic_tree: TopicTree):
        self.llm = llm
        self.topic_tree = topic_tree
        self.min_confidence = 0.5
    
    async def extract(self, memory_item: MemoryItem) -> List[TopicAssignment]:
        # 1. Pre-process
        text = self._clean_text(memory_item.content)
        
        # 2. Build prompt with available topics
        prompt = self._build_prompt(text, self.topic_tree.get_all())
        
        # 3. Call LLM (cheap model)
        response = await self.llm.complete(
            prompt=prompt,
            model="claude-3-haiku",  # cheap and fast
            temperature=0.1
        )
        
        # 4. Parse response
        assignments = self._parse_response(response)
        
        # 5. Validate topics exist
        validated = [
            a for a in assignments 
            if self.topic_tree.exists(a.topic_slug) 
            and a.confidence >= self.min_confidence
        ]
        
        return validated
    
    def _build_prompt(self, text: str, topics: List[Topic]) -> str:
        topic_list = "\n".join([f"- {t.path}: {t.description}" for t in topics])
        return f"""
        Classify the following text into one or more topics.
        
        Available topics:
        {topic_list}
        
        Text:
        {text}
        
        Return JSON array with topic slugs and confidence (0.0-1.0).
        Example: [{{"topic": "finance/budget", "confidence": 0.85}}]
        """
```

---

### 5. Topic Statistics API

```python
class TopicStatistics:
    async def get_activity(
        self, 
        topic_id: UUID,
        days: int = 30
    ) -> TopicActivity:
        """Get activity metrics for a topic"""
        return await self.db.query("""
            SELECT 
                COUNT(*) as item_count,
                COUNT(CASE WHEN item_type = 'decision' THEN 1 END) as decisions,
                COUNT(CASE WHEN item_type = 'insight' THEN 1 END) as insights,
                AVG(mt.confidence) as avg_confidence
            FROM memory_items mi
            JOIN memory_topics mt ON mi.id = mt.memory_id
            WHERE mt.topic_id = $1 
            AND mi.created_at > NOW() - INTERVAL '$2 days'
        """, topic_id, days)
    
    async def get_trends(
        self,
        days: int = 30,
        limit: int = 10
    ) -> List[TopicTrend]:
        """Get topic trends (rising/falling)"""
        # Compare current period vs previous period
        pass
    
    async def get_heatmap(
        self,
        topic_ids: List[UUID] = None,
        weeks: int = 12
    ) -> HeatmapData:
        """Get activity heatmap data"""
        pass
```

---

## ✅ Критерии завершения

- [x] Модель данных тем готова
- [x] Пайплайн обработки описан
- [x] Confidence score интегрирован
- [x] Иерархия тем поддерживается

---

## 📎 Связанные документы

- [TASK 2.1 — Memory Layer Design](./TASK_2.1_Memory_Layer_Design.md)
- [ADR v1.2 — CAL](../../ADR%20v1.2%20—%20Cognitive%20Analytics%20Layer.md)
- [TASK 3.1 — CAL Architecture](../phase-3/TASK_3.1_CAL_Architecture.md)
