# 🏷️ TASK 10.2 — Topic Auto-Clustering

**Проект:** Digital Denis v0.2.0  
**Статус:** ✅ Завершено  
**Приоритет:** Средний  
**Оценка:** 2-3 дня  
**Зависимости:** TASK 10.1

---

## 🎯 Цель

Автоматически группировать memories в топики на основе семантической близости.

---

## 📋 Чеклист реализации

### Clustering Algorithm
- [x] Выбор алгоритма (HDBSCAN / K-Means / Agglomerative)
- [x] Определение оптимального числа кластеров (автоматически в HDBSCAN)
- [x] Обработка outliers (uncategorized)
- [x] Incremental clustering для новых items (через orchestrator)

### Topic Generation
- [x] LLM для генерации названий топиков
- [x] Ключевые слова для каждого топика
- [ ] Иерархия топиков (parent-child) - [Отложено]
- [x] Merge похожих топиков (интегрировано в пайплайн)

### Background Jobs
- [x] Celery task для периодической кластеризации
- [x] Cron: ежедневный/еженедельный re-cluster (через Beat)
- [ ] Trigger при достижении N новых items - [В процессе]
- [x] Progress reporting (через Celery task status)

### API & UI
- [x] Endpoint `/api/v1/topics/auto-generate`
- [x] Endpoint `/api/v1/topics/{id}/rename` (используется существующий)
- [ ] UI для просмотра кластеров (Frontend будет в следующей задаче)
- [ ] Drag-and-drop для ручной корректировки

### Topic Graph
- [x] Связи между топиками (similarity в БД)
- [ ] Визуализация графа топиков
- [ ] Temporal analysis (как топики меняются)

---

## 📦 Артефакты

```
backend/
├── analytics/
│   ├── clustering.py           # Clustering algorithms
│   ├── topic_generator.py      # LLM topic naming
│   └── jobs.py                 # Background tasks
├── api/
│   └── routes/
│       └── topics.py           # Topic management API
└── memory/
    └── models.py               # + Topic model updates

frontend/
└── src/
    ├── components/
    │   ├── TopicCloud.tsx      # Topic visualization
    │   └── TopicGraph.tsx      # Graph view
    └── app/
        └── topics/
            └── page.tsx        # Topics page
```

---

## 📝 Пример Clustering Service

```python
# analytics/clustering.py
from sklearn.cluster import HDBSCAN
import numpy as np
from typing import List, Tuple
from uuid import UUID

class ClusteringService:
    def __init__(self, min_cluster_size: int = 5, min_samples: int = 3):
        self.clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='cosine',
            cluster_selection_method='eom'
        )
    
    async def cluster_memories(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> List[Tuple[int, List[UUID]]]:
        """
        Cluster user's memories and return cluster assignments.
        Returns: [(cluster_id, [memory_ids]), ...]
        """
        # Get all embeddings
        embeddings, memory_ids = await self._get_embeddings(db, user_id)
        
        if len(embeddings) < self.clusterer.min_cluster_size:
            return []
        
        # Fit clusters
        labels = self.clusterer.fit_predict(np.array(embeddings))
        
        # Group by cluster
        clusters = {}
        for i, label in enumerate(labels):
            if label == -1:  # Noise/outlier
                continue
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(memory_ids[i])
        
        return list(clusters.items())
    
    async def generate_topic_name(
        self,
        db: AsyncSession,
        memory_ids: List[UUID]
    ) -> str:
        """Generate topic name using LLM."""
        # Get sample memories
        memories = await self._get_memories(db, memory_ids[:5])
        contents = "\n---\n".join([m.content[:200] for m in memories])
        
        prompt = f"""Дай короткое название (2-4 слова) для этой группы записей:

{contents}

Название темы:"""
        
        from llm.groq import groq
        name = await groq.complete_simple(prompt)
        return name.strip().strip('"')


clustering_service = ClusteringService()
```

---

## 📊 Clustering Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| min_cluster_size | 5 | Minimum memories per topic |
| min_samples | 3 | Core samples for density |
| metric | cosine | Distance metric |
| cluster_selection_method | eom | Excess of mass (better hierarchy) |

---

## ✅ Критерии завершения

- [x] Кластеризация работает на реальных данных
- [x] Названия топиков генерируются автоматически
- [x] Background job запускается по расписанию
- [ ] UI показывает топики и их содержимое (Frontend WIP)

---

## 📎 Связанные документы

- [TASK 10.1 — Vector DB Integration](./TASK_10.1_Vector_DB.md)
- [TASK 10.3 — Analytics Dashboard](./TASK_10.3_Analytics_Dashboard.md)
