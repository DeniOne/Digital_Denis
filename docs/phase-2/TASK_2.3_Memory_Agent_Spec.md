# 🧹 TASK 2.3 — Memory Agent v2

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Средний  
**Зависимости:** TASK 2.1, TASK 2.2

---

## 📋 Чеклист реализации

- [x] Реализовать auto_save() в Memory Agent
- [x] Реализовать extract_candidates() для decisions/insights/facts
- [x] Реализовать забывание с подтверждением
- [x] Реализовать агрегацию (v0.2)
- [x] Интеграция с другими агентами
- [x] Написать unit-тесты

---

## 🎯 Цель

Описать Memory Agent v2: правила сохранения, агрегации, забывания и пересборки памяти.

---

## 📦 Артефакты

### 1. Роль Memory Agent

Memory Agent — специализированный агент для управления памятью системы.

**Ключевые функции:**
- Определение: что сохранять (decision/insight/fact)
- Классификация: с какой уверенностью и темой
- Агрегация: объединение похожих items
- Забывание: контролируемое удаление
- Retrieval: поиск релевантной памяти

---

### 2. Правила сохранения

| Тип контента | Паттерны обнаружения | Auto-save | Confidence |
|--------------|---------------------|-----------|------------|
| **Decision** | "решил", "будем делать", "принял решение" | ✅ | 0.85+ |
| **Insight** | "понял", "осознал", "ключевой момент" | ✅ | 0.75+ |
| **Fact** | "факт:", числа, даты, имена | ✅ | 0.90+ |
| **Thought** | Размышления, гипотезы | ❌ (confirm) | 0.50+ |

**Decision Schema (structured):**
```json
{
  "type": "decision",
  "content": "Увеличить бюджет на маркетинг на 20%",
  "structured_data": {
    "hypothesis": "Рост бюджета приведёт к увеличению конверсии",
    "arguments": [
      "Конкуренты увеличили расходы",
      "ROI маркетинга положительный"
    ],
    "assumptions": [
      "Рынок не изменится",
      "Команда справится с объёмом"
    ],
    "counterarguments": [
      "Риск отсутствия результата"
    ],
    "confidence": 0.8
  }
}
```

---

### 3. Правила агрегации

| Триггер | Условие | Действие |
|---------|---------|----------|
| **Similar content** | Cosine similarity > 0.85 | Merge into summary |
| **Same topic + period** | >10 items за неделю | Create weekly digest |
| **Stale + low access** | >90 дней, <3 accesses | Archive with summary |

**Aggregation process:**
```python
class MemoryAggregator:
    async def aggregate_similar(
        self, 
        items: List[MemoryItem],
        threshold: float = 0.85
    ) -> MemoryItem:
        # 1. Group by similarity
        clusters = self._cluster_by_similarity(items, threshold)
        
        # 2. For each cluster, generate summary
        aggregated = []
        for cluster in clusters:
            if len(cluster) > 1:
                summary = await self._generate_summary(cluster)
                aggregated_item = MemoryItem(
                    item_type="aggregation",
                    content=summary,
                    structured_data={"source_ids": [i.id for i in cluster]}
                )
                aggregated.append(aggregated_item)
                
                # Archive originals
                for item in cluster:
                    item.status = "aggregated"
                    
        return aggregated
```

---

### 4. Правила забывания

| Критерий | Срок | Действие | Reversible |
|----------|------|----------|------------|
| **Explicit request** | Immediate | Soft delete | ✅ 30 дней |
| **Low relevance** | 180 дней | Archive | ✅ |
| **Duplicate** | On detection | Merge | ✅ |
| **Contradiction** | On detection | Flag for review | N/A |

**Forget confirmation flow:**
```
User: "Забудь решение о бюджете от 15 января"

Memory Agent:
"Найдено решение: 'Увеличить бюджет на маркетинг на 20%' от 15.01.2024.

⚠️ Это решение связано с:
- 3 другими решениями
- 2 инсайтами

Подтвердите удаление? Восстановление возможно в течение 30 дней."

User: "Да"

Memory Agent: "Решение перемещено в архив. Связанные элементы сохранены."
```

---

### 5. Правила пересборки

| Сценарий | Триггер | Процесс |
|----------|---------|---------|
| **Full reindex** | Manual / Admin | Rebuild all embeddings |
| **Topic reassignment** | Topic tree change | Re-classify affected items |
| **Contradiction resolution** | User decision | Update conflicting items |

---

### 6. Memory Agent API

```python
class MemoryAgentV2(BaseAgent):
    """Memory management agent"""
    
    async def process(self, context: AgentContext) -> AgentResponse:
        # Determine operation type
        operation = self._classify_operation(context.message)
        
        if operation == "search":
            return await self._handle_search(context)
        elif operation == "save":
            return await self._handle_save(context)
        elif operation == "forget":
            return await self._handle_forget(context)
        elif operation == "aggregate":
            return await self._handle_aggregate(context)
        else:
            return await self._default_response(context)
    
    async def auto_save(
        self, 
        agent_response: AgentResponse,
        context: AgentContext
    ) -> List[MemoryAction]:
        """
        Called after other agents respond.
        Determines what should be saved from the interaction.
        """
        # 1. Extract potential memory items from response
        candidates = await self._extract_candidates(agent_response.content)
        
        # 2. Filter by confidence threshold
        to_save = [c for c in candidates if c.confidence >= self.min_confidence]
        
        # 3. Check for duplicates
        unique = await self._deduplicate(to_save)
        
        # 4. Generate memory actions
        actions = []
        for item in unique:
            actions.append(MemoryAction(
                type="save",
                item_type=item.type,
                content=item.content,
                confidence=item.confidence
            ))
            
        return actions
    
    async def _extract_candidates(
        self, 
        content: str
    ) -> List[MemoryCandidate]:
        """Use LLM to extract saveable items"""
        prompt = f"""
        Analyze this conversation response and identify:
        1. Decisions (explicit choices made)
        2. Insights (realizations, learnings)
        3. Facts (specific data, numbers, dates)
        
        Response:
        {content}
        
        Return JSON array with type, content, and confidence.
        """
        result = await self.llm.complete(prompt, model="claude-3-haiku")
        return self._parse_candidates(result)
```

---

### 7. Integration with Other Agents

```
┌────────────────────────────────────────────────────────────────────┐
│                  MEMORY AGENT INTEGRATION                          │
└────────────────────────────────────────────────────────────────────┘

             ┌──────────────┐
             │ Core Agent   │
             │ (response)   │
             └──────┬───────┘
                    │
                    ▼
        ┌───────────────────────┐
        │    Memory Agent       │
        │    .auto_save()       │
        │  ┌─────────────────┐  │
        │  │ Extract items   │  │
        │  │ Classify type   │  │
        │  │ Check duplicates│  │
        │  │ Generate actions│  │
        │  └─────────────────┘  │
        └───────────┬───────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐      ┌───────────────┐
│   PostgreSQL  │      │   Vector DB   │
│   (persist)   │      │   (index)     │
└───────────────┘      └───────────────┘
        │
        ▼
┌───────────────┐
│   CAL Queue   │
│ (topic extract)│
└───────────────┘
```

---

## ✅ Критерии завершения

- [x] Правила сохранения формализованы
- [x] Агрегация автоматизирована
- [x] Забывание контролируемо
- [x] Пересборка возможна

---

## 📎 Связанные документы

- [TASK 2.1 — Memory Layer Design](./TASK_2.1_Memory_Layer_Design.md)
- [TASK 1.3 — Agent Specification](../phase-1/TASK_1.3_Agent_Specification.md)
- [TASK 3.1 — CAL Architecture](../phase-3/TASK_3.1_CAL_Architecture.md)
