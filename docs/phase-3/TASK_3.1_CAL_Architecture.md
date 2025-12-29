# 🧠 TASK 3.1 — CAL Architecture

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Средний  
**Зависимости:** TASK 2.3

---

## 📋 Чеклист реализации (v1.0)

- [ ] Создать backend/analytics/__init__.py
- [ ] Настроить Celery workers для CAL
- [ ] Реализовать CALService
- [ ] Создать таблицы cal_* в PostgreSQL
- [ ] Интеграция с Memory Layer (hooks)
- [ ] Написать integration-тесты

---

## 🎯 Цель

Спроектировать Cognitive Analytics Layer: компоненты, входы, выходы, асинхронность.

---

## 📦 Артефакты

### 1. Архитектура CAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COGNITIVE ANALYTICS LAYER (CAL)                          │
│                     "Мета-уровень анализа мышления"                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐                                                           │
│   │ Memory Layer│──────────────────┐                                        │
│   └─────────────┘                  │                                        │
│                                    ▼                                        │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │                         CAL INPUT QUEUE                            │   │
│   │                      (Redis / RabbitMQ)                            │   │
│   └─────────────────────────────────┬──────────────────────────────────┘   │
│                                     │                                       │
│         ┌───────────────┬───────────┴───────────┬───────────────┐          │
│         ▼               ▼                       ▼               ▼          │
│   ┌───────────┐   ┌───────────┐   ┌─────────────────┐   ┌───────────┐     │
│   │  TOPIC    │   │   MIND    │   │     LOGIC       │   │ ANOMALY   │     │
│   │INTELLIGENCE│  │   MAPS    │   │   ANALYSIS      │   │ DETECTION │     │
│   │           │   │           │   │                 │   │           │     │
│   │ Extract   │   │ Build     │   │ Evaluate        │   │ Compare   │     │
│   │ Classify  │   │ Connect   │   │ decisions       │   │ Detect    │     │
│   │ Trend     │   │ Visualize │   │ Find gaps       │   │ Alert     │     │
│   └─────┬─────┘   └─────┬─────┘   └────────┬────────┘   └─────┬─────┘     │
│         │               │                  │                   │           │
│         └───────────────┴─────────┬────────┴───────────────────┘           │
│                                   ▼                                         │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │                      CAL OUTPUT STORE                              │   │
│   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │   │
│   │   │ topic_stats  │  │ graph_data   │  │  anomalies   │            │   │
│   │   └──────────────┘  └──────────────┘  └──────────────┘            │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │                        FRONTEND UI                                  │   │
│   │   Topic Explorer │ Mind Map View │ Decision Inspector │ Health     │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2. Компоненты CAL

| Компонент | Назначение | Sync/Async | Trigger |
|-----------|------------|------------|---------|
| **Topic Intelligence** | Классификация памяти по темам, тренды | Async | New memory item |
| **Mind Maps** | Граф связей между идеями/решениями | Async | Batch (5 min) |
| **Logic Analysis** | Анализ качества решений | Async | New decision |
| **Anomaly Detection** | Выявление отклонений от нормы | Async | Hourly + on-demand |

---

### 3. Входы и выходы

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         CAL DATA FLOW                                     │
└──────────────────────────────────────────────────────────────────────────┘

INPUTS                          PROCESSING                       OUTPUTS
───────                         ──────────                       ───────

┌───────────────┐
│ New Memory    │──┐
│ Item          │  │
└───────────────┘  │
                   │            ┌─────────────────┐
┌───────────────┐  │            │                 │            ┌──────────────┐
│ Memory Items  │──┼───────────>│ Topic Intel     │───────────>│ Topic Stats  │
│ (batch)       │  │            │                 │            │ Topic Links  │
└───────────────┘  │            └─────────────────┘            └──────────────┘
                   │
                   │            ┌─────────────────┐            ┌──────────────┐
┌───────────────┐  │            │                 │            │ Graph Nodes  │
│ Existing      │──┼───────────>│ Mind Maps       │───────────>│ Graph Edges  │
│ Graph         │  │            │                 │            │ Clusters     │
└───────────────┘  │            └─────────────────┘            └──────────────┘
                   │
                   │            ┌─────────────────┐            ┌──────────────┐
┌───────────────┐  │            │                 │            │ Decision     │
│ Decisions     │──┼───────────>│ Logic Analysis  │───────────>│ Reports      │
│ (structured)  │  │            │                 │            │ Risk Flags   │
└───────────────┘  │            └─────────────────┘            └──────────────┘
                   │
                   │            ┌─────────────────┐            ┌──────────────┐
┌───────────────┐  │            │                 │            │ Anomaly      │
│ Historical    │──┴───────────>│ Anomaly Detect  │───────────>│ Alerts       │
│ Baseline      │               │                 │            │ Trends       │
└───────────────┘               └─────────────────┘            └──────────────┘
```

---

### 4. Асинхронная обработка

```python
# workers/cal_tasks.py
from celery import Celery

app = Celery('cal', broker='redis://localhost:6379/0')

@app.task(queue='topics')
def extract_topics(memory_item_id: str):
    """Extract and assign topics to memory item"""
    item = get_memory_item(memory_item_id)
    topics = topic_extractor.extract(item)
    save_topic_assignments(item.id, topics)
    update_topic_stats(topics)

@app.task(queue='graphs')
def update_graph(memory_item_ids: List[str]):
    """Update mind map graph with new items"""
    items = get_memory_items(memory_item_ids)
    new_edges = graph_builder.find_connections(items)
    save_graph_edges(new_edges)

@app.task(queue='analytics')
def analyze_decision(decision_id: str):
    """Analyze decision quality and risks"""
    decision = get_decision(decision_id)
    analysis = logic_analyzer.analyze(decision)
    save_decision_analysis(decision.id, analysis)

@app.task(queue='analytics')
def detect_anomalies():
    """Periodic anomaly detection"""
    baseline = get_baseline(days=30)
    current = get_current_metrics(days=7)
    anomalies = anomaly_detector.compare(baseline, current)
    for anomaly in anomalies:
        create_anomaly_alert(anomaly)

# Periodic schedule
app.conf.beat_schedule = {
    'detect-anomalies-hourly': {
        'task': 'workers.cal_tasks.detect_anomalies',
        'schedule': 3600.0,  # every hour
    },
    'update-graph-batch': {
        'task': 'workers.cal_tasks.update_graph_batch',
        'schedule': 300.0,  # every 5 minutes
    },
}
```

---

### 5. CAL Database Schema

```sql
-- Topic statistics (time-series)
CREATE TABLE cal_topic_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID REFERENCES topics(id),
    period_date DATE NOT NULL,
    item_count INTEGER DEFAULT 0,
    decision_count INTEGER DEFAULT 0,
    insight_count INTEGER DEFAULT 0,
    avg_confidence FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Graph storage
CREATE TABLE cal_graph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID REFERENCES memory_items(id),
    node_type VARCHAR(50),  -- idea, decision, insight, topic
    label TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE cal_graph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES cal_graph_nodes(id),
    target_id UUID REFERENCES cal_graph_nodes(id),
    edge_type VARCHAR(50),  -- depends_on, contradicts, evolves_from, reinforces
    weight FLOAT DEFAULT 1.0,
    confidence FLOAT DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Decision analysis results
CREATE TABLE cal_decision_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID REFERENCES memory_items(id),
    strong_points JSONB,
    weak_points JSONB,
    risks JSONB,
    overall_score FLOAT,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Anomaly alerts
CREATE TABLE cal_anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anomaly_type VARCHAR(50),
    severity VARCHAR(20),  -- low, medium, high
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    baseline_value FLOAT,
    current_value FLOAT,
    deviation_percent FLOAT,
    interpretation TEXT,
    status VARCHAR(20) DEFAULT 'new',  -- new, acknowledged, resolved
    acknowledged_at TIMESTAMP WITH TIME ZONE
);
```

---

### 6. CAL Service Interface

```python
class CALService:
    """Cognitive Analytics Layer service"""
    
    def __init__(self):
        self.topic_intel = TopicIntelligence()
        self.mind_maps = MindMapBuilder()
        self.logic_analyzer = LogicAnalyzer()
        self.anomaly_detector = AnomalyDetector()
    
    # Sync: called from Memory Layer
    async def on_memory_created(self, memory_id: UUID):
        """Trigger CAL processing for new memory item"""
        # Queue topic extraction
        extract_topics.delay(str(memory_id))
        
        # If decision, queue analysis
        item = await self.memory.get(memory_id)
        if item.item_type == 'decision':
            analyze_decision.delay(str(memory_id))
    
    # API: for frontend
    async def get_topic_trends(
        self, 
        days: int = 30
    ) -> List[TopicTrend]:
        """Get topic activity trends"""
        pass
    
    async def get_mind_map(
        self,
        topic_id: UUID = None,
        days: int = 30
    ) -> GraphData:
        """Get mind map graph data"""
        pass
    
    async def get_anomalies(
        self,
        status: str = 'new'
    ) -> List[Anomaly]:
        """Get current anomalies"""
        pass
    
    async def get_cognitive_health(self) -> CognitiveHealthReport:
        """Get overall cognitive health report"""
        pass
```

---

## ✅ Критерии завершения

- [x] Все компоненты CAL описаны
- [x] Входы/выходы формализованы
- [x] Асинхронность спроектирована
- [x] Соответствует ADR v1.2

---

## 📎 Связанные документы

- [ADR v1.2 — Cognitive Analytics Layer](../../ADR%20v1.2%20—%20Cognitive%20Analytics%20Layer.md)
- [TASK 2.3 — Memory Agent Spec](../phase-2/TASK_2.3_Memory_Agent_Spec.md)
- [TASK 3.2 — Mind Map Graph](./TASK_3.2_Mind_Map_Graph.md)
