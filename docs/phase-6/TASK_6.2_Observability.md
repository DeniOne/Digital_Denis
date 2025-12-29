# 👁️ TASK 6.2 — Observability & Audit

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Средний  
**Зависимости:** TASK 6.1

---

## 📋 Чеклист реализации

- [ ] Настроить structlog
- [ ] Создать audit trail таблицу
- [ ] Логировать все критические события
- [ ] Prometheus metrics endpoint
- [ ] Grafana dashboards (опционально)
- [ ] Log retention policy настроена

---

## 🎯 Цель

Описать систему логирования и аудита.

---

## 📦 Артефакт: Observability Plan

### Logging Levels

| Level | Use Case | Retention |
|-------|----------|-----------|
| DEBUG | Development only | 1 day |
| INFO | Normal operations | 7 days |
| WARNING | Anomalies | 30 days |
| ERROR | Failures | 90 days |
| CRITICAL | System failures | 1 year |

---

### What Gets Logged

| Event | Level | Data |
|-------|-------|------|
| User message | INFO | timestamp, length |
| Agent selection | INFO | agent_type, reason |
| Memory save | INFO | item_id, type |
| LLM call | INFO | model, tokens, latency |
| Anomaly detected | WARNING | type, severity |
| Error | ERROR | stack trace, context |

---

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "message_processed",
    session_id=session_id,
    agent="core",
    latency_ms=1250,
    tokens_used=450
)

# Output (JSON)
{
    "event": "message_processed",
    "session_id": "uuid",
    "agent": "core",
    "latency_ms": 1250,
    "tokens_used": 450,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Audit Trail

| Action | Captured | Retention |
|--------|----------|-----------|
| Login | user, timestamp, method | 1 year |
| Memory modification | before/after, user | 1 year |
| Settings change | field, old/new value | 1 year |
| Export data | timestamp, scope | 1 year |

---

### Metrics (Prometheus)

| Metric | Type | Description |
|--------|------|-------------|
| `llm_latency_seconds` | Histogram | LLM response time |
| `memory_items_total` | Counter | Total memory items |
| `active_sessions` | Gauge | Current sessions |
| `anomalies_detected` | Counter | Anomaly count |

---

## ✅ Критерии завершения

- [x] Logging levels определены
- [x] Audit trail спроектирован
- [x] Metrics описаны

---

## 📎 Связанные документы

- [TASK 6.1 — Security Architecture](./TASK_6.1_Security_Architecture.md)
