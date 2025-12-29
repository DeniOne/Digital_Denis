# ⚠️ TASK 3.4 — Anomaly Detection Engine

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Средний  
**Зависимости:** TASK 3.1

---

## 📋 Чеклист реализации (v1.0)

- [x] Создать backend/analytics/anomalies.py
- [x] Реализовать AnomalyDetector
- [x] Реализовать baseline calculation
- [x] Создать таблицу cal_anomalies
- [x] Celery task detect_anomalies (hourly)
- [x] API endpoint /analytics/anomalies
- [x] Написать unit-тесты

---

## 🎯 Цель

Описать механизм выявления аномалий мышления: baseline, метрики, типы отклонений.

---

## 📦 Артефакты

### 1. Baseline Configuration

| Параметр | Период | Описание |
|----------|--------|----------|
| **Short baseline** | 7 дней | Недельная норма (сравнение "вчера vs неделя") |
| **Medium baseline** | 30 дней | Месячная норма (основной) |
| **Long baseline** | 90 дней | Квартальная норма (стратегические тренды) |

---

### 2. Анализируемые метрики

| Метрика | Описание | Нормальный диапазон | Единица |
|---------|----------|---------------------|---------|
| `topic_frequency` | Частота тем | ± 2σ от baseline | % от общего |
| `decision_rate` | Кол-во решений | 5-15 в неделю | решений/неделя |
| `confidence_avg` | Средняя уверенность | 0.6 - 0.85 | 0.0 - 1.0 |
| `decision_quality` | Качество решений | 0.65 - 0.90 | score |
| `topic_diversity` | Разнообразие тем | 3-8 активных | кол-во |
| `response_depth` | Глубина анализа | tokens/decision | средняя |

---

### 3. Типы аномалий

| Тип | Триггер | Severity | Интерпретация |
|-----|---------|----------|---------------|
| **Topic Spike** | Тема +50% за 7 дней | 🟡 Medium | Повышенное внимание к области |
| **Topic Disappearance** | Ключевая тема -70% | 🟡 Medium | Возможное избегание |
| **Decision Surge** | Решений x2 от нормы | 🟠 High | Возможная импульсивность |
| **Decision Drought** | Решений <30% нормы | 🟡 Medium | Возможный ступор |
| **Confidence Spike** | Уверенность +30% | 🟡 Medium | Возможная самонадеянность |
| **Confidence Drop** | Уверенность -30% | 🟠 High | Возможная неуверенность |
| **Quality Degradation** | Качество -20% | 🔴 Critical | Деградация мышления |
| **Topic Narrowing** | Разнообразие <3 | 🟡 Medium | Туннельное видение |

---

### 4. Anomaly Detector Implementation

```python
class AnomalyDetector:
    def __init__(self):
        self.thresholds = {
            'topic_spike': 0.5,      # +50%
            'topic_drop': 0.7,       # -70%
            'decision_surge': 2.0,   # x2
            'confidence_shift': 0.3, # ±30%
            'quality_drop': 0.2      # -20%
        }
    
    async def detect(self) -> List[Anomaly]:
        anomalies = []
        
        # Get baselines
        baseline_30 = await self._get_baseline(days=30)
        current_7 = await self._get_current(days=7)
        
        # Check topic anomalies
        topic_anomalies = self._check_topics(baseline_30, current_7)
        anomalies.extend(topic_anomalies)
        
        # Check decision rate
        decision_anomalies = self._check_decisions(baseline_30, current_7)
        anomalies.extend(decision_anomalies)
        
        # Check confidence
        confidence_anomalies = self._check_confidence(baseline_30, current_7)
        anomalies.extend(confidence_anomalies)
        
        # Get LLM interpretation
        for anomaly in anomalies:
            anomaly.interpretation = await self._interpret(anomaly)
        
        return anomalies
    
    def _check_topics(self, baseline, current) -> List[Anomaly]:
        anomalies = []
        
        for topic_id, current_freq in current.topic_frequencies.items():
            baseline_freq = baseline.topic_frequencies.get(topic_id, 0)
            
            if baseline_freq > 0:
                change = (current_freq - baseline_freq) / baseline_freq
                
                if change > self.thresholds['topic_spike']:
                    anomalies.append(Anomaly(
                        type='topic_spike',
                        severity='medium',
                        topic_id=topic_id,
                        baseline_value=baseline_freq,
                        current_value=current_freq,
                        deviation_percent=change * 100
                    ))
                elif change < -self.thresholds['topic_drop']:
                    anomalies.append(Anomaly(
                        type='topic_disappearance',
                        severity='medium',
                        topic_id=topic_id,
                        baseline_value=baseline_freq,
                        current_value=current_freq,
                        deviation_percent=change * 100
                    ))
        
        return anomalies
    
    async def _interpret(self, anomaly: Anomaly) -> str:
        """Use LLM to generate human-readable interpretation"""
        prompt = f"""
        Anomaly detected: {anomaly.type}
        Topic: {anomaly.topic_name}
        Change: {anomaly.deviation_percent:.1f}%
        
        Provide a brief, non-judgmental interpretation of what this 
        might indicate about thinking patterns. Keep it neutral.
        """
        return await self.llm.complete(prompt, model="claude-3-haiku")
```

---

### 5. Anomaly Storage & UI

```sql
CREATE TABLE anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    
    -- Context
    topic_id UUID REFERENCES topics(id),
    metric_name VARCHAR(50),
    
    -- Values
    baseline_value FLOAT,
    current_value FLOAT,
    deviation_percent FLOAT,
    
    -- Interpretation
    interpretation TEXT,
    recommendation TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'new',
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_note TEXT,
    
    detected_at TIMESTAMP DEFAULT NOW()
);
```

**UI Alert Format:**
```
┌────────────────────────────────────────────────────────────────┐
│ 🟠 Decision Surge Detected                          2 часа назад│
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ За последнюю неделю принято 23 решения (норма: 8-12).          │
│                                                                 │
│ 📊 Baseline: 10 решений/неделя                                  │
│ 📈 Текущее: 23 решения (+130%)                                  │
│                                                                 │
│ 💭 Интерпретация:                                               │
│ Повышенная активность в принятии решений может указывать       │
│ на период высокой вовлечённости или на импульсивность.         │
│ Рекомендуется проверить качество недавних решений.             │
│                                                                 │
│ [✓ Подтвердить]  [📝 Добавить заметку]  [⏰ Напомнить позже]    │
└────────────────────────────────────────────────────────────────┘
```

---

## ✅ Критерии завершения

- [x] Baseline сконфигурирован
- [x] Метрики определены
- [x] Типы аномалий каталогизированы
- [x] Интерпретация human-readable

---

## 📎 Связанные документы

- [TASK 3.1 — CAL Architecture](./TASK_3.1_CAL_Architecture.md)
- [TASK 5.2 — UI Wireframes](../phase-5/TASK_5.2_UI_Wireframes.md)
