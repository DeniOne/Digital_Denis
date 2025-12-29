# ⚙️ TASK 4.2 — Async & Background Jobs

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Средний  
**Зависимости:** TASK 4.1

---

## 📋 Чеклист реализации

- [ ] Настроить Celery с Redis
- [ ] Создать backend/workers/tasks.py
- [ ] Реализовать все Celery tasks
- [ ] Настроить periodic schedule (beat)
- [ ] Docker service для worker
- [ ] Мониторинг очередей (Flower)

---

## 🎯 Цель

Описать фоновые задачи: какие асинхронные, какие синхронные.

---

## 📦 Артефакт: Background Jobs Map

### Синхронные задачи (Request-Response)

| Задача | Endpoint | Max Latency | Notes |
|--------|----------|-------------|-------|
| Get current context | `/messages/session/{id}` | <100ms | Redis cache |
| Send message | `POST /messages` | <5s | LLM call |
| Get memory item | `/memory/{id}` | <100ms | DB query |
| Get memory list | `/memory` | <200ms | Paginated |
| Get topics tree | `/topics/tree` | <150ms | Cached |
| Get graph | `/graph` | <500ms | Limited nodes |

---

### Асинхронные задачи (Background)

| Задача | Очередь | Триггер | Priority |
|--------|---------|---------|----------|
| `extract_topics` | `topics` | New memory item | High |
| `update_embeddings` | `embeddings` | New/updated item | High |
| `analyze_decision` | `analytics` | New decision | Medium |
| `update_graph` | `graphs` | Batch (5 min) | Low |
| `detect_anomalies` | `analytics` | Hourly | Low |
| `aggregate_memory` | `memory` | Daily (2am) | Low |
| `cleanup_sessions` | `maintenance` | Hourly | Low |

---

### Очереди (Queues)

| Queue | Workers | Concurrency | Description |
|-------|---------|-------------|-------------|
| `default` | 2 | 4 | General purpose |
| `topics` | 1 | 2 | Topic extraction |
| `embeddings` | 1 | 2 | Vector indexing |
| `analytics` | 1 | 1 | CAL processing |
| `graphs` | 1 | 1 | Graph updates |
| `memory` | 1 | 1 | Memory ops |
| `maintenance` | 1 | 1 | Cleanup jobs |

---

### Task Definitions (Celery)

```python
# workers/tasks.py
from celery import Celery

app = Celery('digital_denis')

# High priority - per item
@app.task(queue='topics', priority=8)
def extract_topics(memory_id: str):
    """Extract and assign topics"""
    pass

@app.task(queue='embeddings', priority=8)
def update_embeddings(memory_id: str):
    """Update vector embeddings"""
    pass

# Medium priority - on decision
@app.task(queue='analytics', priority=5)
def analyze_decision(decision_id: str):
    """Analyze decision quality"""
    pass

# Low priority - batch/periodic
@app.task(queue='graphs', priority=2)
def update_graph_batch():
    """Update graph connections (batch)"""
    pass

@app.task(queue='analytics', priority=2)
def detect_anomalies():
    """Periodic anomaly detection"""
    pass

@app.task(queue='memory', priority=1)
def aggregate_memory():
    """Daily memory aggregation"""
    pass
```

---

### Periodic Schedule

```python
app.conf.beat_schedule = {
    'detect-anomalies': {
        'task': 'workers.tasks.detect_anomalies',
        'schedule': 3600.0,  # hourly
    },
    'update-graph': {
        'task': 'workers.tasks.update_graph_batch',
        'schedule': 300.0,  # 5 min
    },
    'aggregate-memory': {
        'task': 'workers.tasks.aggregate_memory',
        'schedule': crontab(hour=2, minute=0),  # 2am daily
    },
    'cleanup-sessions': {
        'task': 'workers.tasks.cleanup_sessions',
        'schedule': 3600.0,  # hourly
    },
}
```

---

### Retry Policy

| Задача | Max Retries | Backoff | Notes |
|--------|-------------|---------|-------|
| extract_topics | 3 | Exponential (1m, 5m, 30m) | LLM may fail |
| update_embeddings | 3 | Linear (1m) | Vector DB may be slow |
| analyze_decision | 2 | Exponential | LLM intensive |
| update_graph | 1 | None | Best effort |
| detect_anomalies | 2 | Linear (5m) | Can wait |

---

## ✅ Критерии завершения

- [x] Все задачи классифицированы
- [x] Очереди определены
- [x] Приоритеты установлены
- [x] Retry policy описана

---

## 📎 Связанные документы

- [TASK 4.1 — API Contracts](./TASK_4.1_API_Contracts.md)
- [TASK 3.1 — CAL Architecture](../phase-3/TASK_3.1_CAL_Architecture.md)
