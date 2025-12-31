# TASK: Страница настроек AI Control
## Digital Denis v0.2.0

> **Статус:** 📋 Планирование  
> **Приоритет:** Высокий  
> **Основа:** [Options.md](./Options.md)

---

## 📌 Обзор задачи

Создать полноценную страницу настроек `/settings`, которая позволит пользователю управлять:
- Поведением ИИ (роль, стиль мышления, конфронтация)
- Автономностью (инициатива, частота, разрешённые действия)
- Памятью (типы данных, политика хранения)
- Аналитикой (типы анализа, агрессивность)
- Rules Engine (глобальные и контекстные правила)

---

## 🗂️ Карта изменений по компонентам

### 1. BACKEND — База данных

| Файл | Действие | Описание |
|------|----------|----------|
| `backend/memory/models.py` | MODIFY | Добавить модель `UserSettings` |
| `backend/analytics/cal_models.py` | MODIFY | Добавить модель `Rule` для Rules Engine |
| `backend/alembic/versions/xxx_add_settings.py` | NEW | Миграция для новых таблиц |

#### Новые модели:

```python
# UserSettings — настройки пользователя
class UserSettings(Base):
    user_id: UUID (FK → users.id, unique)
    
    # Behavior
    ai_role: str  # partner_strategic, analyst_logical, coach_socratic, recorder_passive, explorer_hypothesis
    thinking_depth: str  # shallow, structured, systemic, philosophical
    response_style: str  # short, detailed
    confrontation_level: str  # none, soft, argumented, hard
    
    # Autonomy
    initiative_level: str  # request_only, suggest, warn, proactive
    intervention_frequency: str  # realtime, post_session, daily_review, anomaly_detected
    allowed_actions: JSONB  # ['create_decisions', 'link_memories', ...]
    
    # Memory
    save_policy: str  # save_all, save_confirmed, save_marked
    auto_archive_days: int
    memory_trust_level: str  # none, cautious, trusted
    
    # Analytics
    analytics_types: JSONB  # ['logical_contradictions', 'recurring_topics', ...]
    analytics_aggressiveness: str  # inform, recommend, warn, demand_attention

# Rule — правила пользователя
class Rule(Base):
    user_id: UUID (FK → users.id)
    scope: str  # global, context
    trigger: str  # always, topic, mode, session
    instruction: Text  # свободный текст
    priority: str  # low, normal, high
    is_active: bool
    context_topic_id: UUID (FK → topics.id, nullable)
    created_at, updated_at
```

---

### 2. BACKEND — API Endpoints

| Файл | Действие | Описание |
|------|----------|----------|
| `backend/api/routes/settings.py` | NEW | Новый роутер для настроек |
| `backend/api/routes/__init__.py` | MODIFY | Подключить settings router |

#### Новые эндпоинты:

```
GET    /api/v1/settings              — получить все настройки пользователя
PUT    /api/v1/settings              — обновить настройки
PATCH  /api/v1/settings/behavior     — обновить только поведение
PATCH  /api/v1/settings/autonomy     — обновить только автономность
PATCH  /api/v1/settings/memory       — обновить только память
PATCH  /api/v1/settings/analytics    — обновить только аналитику

GET    /api/v1/rules                 — список правил
POST   /api/v1/rules                 — создать правило
PUT    /api/v1/rules/{id}            — обновить правило
DELETE /api/v1/rules/{id}            — удалить правило
PATCH  /api/v1/rules/{id}/toggle     — вкл/выкл правило
```

---

### 3. BACKEND — Интеграция с агентами

| Файл | Действие | Описание |
|------|----------|----------|
| `backend/orchestrator/profile.py` | MODIFY | Загружать настройки из БД |
| `backend/orchestrator/router.py` | MODIFY | Применять настройки к контексту |
| `backend/agents/base.py` | MODIFY | Добавить settings в AgentContext |

#### Логика интеграции:
1. При каждом запросе загружаются настройки пользователя
2. Настройки влияют на system prompt
3. Rules Engine правила добавляются в контекст
4. Агенты учитывают настройки при генерации ответов

---

### 4. FRONTEND — API клиент

| Файл | Действие | Описание |
|------|----------|----------|
| `frontend/src/lib/api.ts` | MODIFY | Добавить settingsApi и rulesApi |
| `frontend/src/lib/hooks.ts` | MODIFY | Добавить useSettings, useRules хуки |

---

### 5. FRONTEND — Страница настроек

| Файл | Действие | Описание |
|------|----------|----------|
| `frontend/src/app/settings/page.tsx` | NEW | Главная страница настроек |
| `frontend/src/app/settings/layout.tsx` | NEW | Layout с боковым меню секций |

---

### 6. FRONTEND — Компоненты

| Файл | Действие | Описание |
|------|----------|----------|
| `frontend/src/components/settings/BehaviorSettings.tsx` | NEW | Секция "Поведение ИИ" |
| `frontend/src/components/settings/AutonomySettings.tsx` | NEW | Секция "Автономность" |
| `frontend/src/components/settings/MemorySettings.tsx` | NEW | Секция "Память" |
| `frontend/src/components/settings/AnalyticsSettings.tsx` | NEW | Секция "Аналитика" |
| `frontend/src/components/settings/RulesEngine.tsx` | NEW | Секция "Правила" |
| `frontend/src/components/settings/RuleEditor.tsx` | NEW | Редактор одного правила |
| `frontend/src/components/ui/SettingsCard.tsx` | NEW | Карточка настройки |
| `frontend/src/components/ui/SettingsSelect.tsx` | NEW | Селект для настроек |
| `frontend/src/components/ui/SettingsSlider.tsx` | NEW | Слайдер с метками |

---

### 7. FRONTEND — Навигация

| Файл | Действие | Описание |
|------|----------|----------|
| `frontend/src/components/layout/Sidebar.tsx` | MODIFY | Добавить ссылку на /settings |

---

## 📋 Чек-лист имплементации

### Фаза 1: Backend — Модели и миграции
- [ ] Добавить модель `UserSettings` в `memory/models.py`
- [ ] Добавить модель `Rule` в `cal_models.py`
- [ ] Создать миграцию Alembic
- [ ] Применить миграцию к БД

### Фаза 2: Backend — API
- [ ] Создать `api/routes/settings.py` с эндпоинтами настроек
- [ ] Добавить CRUD для правил
- [ ] Подключить router в `api/routes/__init__.py`
- [ ] Протестировать эндпоинты через curl/Swagger

### Фаза 3: Backend — Интеграция
- [ ] Модифицировать `orchestrator/profile.py` для загрузки настроек
- [ ] Добавить settings в `AgentContext` (`agents/base.py`)
- [ ] Применять правила в `orchestrator/router.py`
- [ ] Тестировать влияние настроек на ответы ИИ

### Фаза 4: Frontend — API и хуки
- [ ] Добавить `settingsApi` в `lib/api.ts`
- [ ] Добавить `rulesApi` в `lib/api.ts`
- [ ] Создать `useSettings` хук
- [ ] Создать `useRules` хук
- [ ] Создать мутации для обновления

### Фаза 5: Frontend — UI компоненты
- [ ] Создать `SettingsCard.tsx`
- [ ] Создать `SettingsSelect.tsx`
- [ ] Создать `SettingsSlider.tsx`

### Фаза 6: Frontend — Секции настроек
- [ ] Создать `BehaviorSettings.tsx`
- [ ] Создать `AutonomySettings.tsx`
- [ ] Создать `MemorySettings.tsx`
- [ ] Создать `AnalyticsSettings.tsx`
- [ ] Создать `RulesEngine.tsx`
- [ ] Создать `RuleEditor.tsx`

### Фаза 7: Frontend — Страница
- [ ] Создать `app/settings/page.tsx`
- [ ] Создать `app/settings/layout.tsx`
- [ ] Добавить ссылку в Sidebar
- [ ] Локализовать все тексты на русский

### Фаза 8: Тестирование
- [ ] Проверить сохранение настроек
- [ ] Проверить применение настроек в чате
- [ ] Проверить CRUD правил
- [ ] Проверить мобильную адаптивность

---

## 🎨 UI/UX структура страницы

```
/settings
├── Боковое меню (tabs)
│   ├── 🤖 Поведение ИИ
│   ├── 🎯 Автономность
│   ├── 🧠 Память
│   ├── 📊 Аналитика
│   └── 📜 Правила
│
└── Контент секции
    ├── Заголовок + описание
    ├── Карточки настроек
    └── Кнопка "Сохранить"
```

---

## ⚠️ Риски и зависимости

| Риск | Митигация |
|------|-----------|
| Сложная миграция БД | Создать backup перед применением |
| Конфликт настроек с существующим profile.py | Сохранить fallback на default profile |
| Производительность (загрузка настроек на каждый запрос) | Кэшировать в Redis |

---

## 📁 Полный список затрагиваемых файлов

### Новые файлы (NEW)
```
backend/
├── api/routes/settings.py
└── alembic/versions/xxx_add_settings.py

frontend/src/
├── app/settings/
│   ├── page.tsx
│   └── layout.tsx
└── components/settings/
    ├── BehaviorSettings.tsx
    ├── AutonomySettings.tsx
    ├── MemorySettings.tsx
    ├── AnalyticsSettings.tsx
    ├── RulesEngine.tsx
    └── RuleEditor.tsx
```

### Изменяемые файлы (MODIFY)
```
backend/
├── memory/models.py
├── analytics/cal_models.py
├── api/routes/__init__.py
├── orchestrator/profile.py
├── orchestrator/router.py
└── agents/base.py

frontend/src/
├── lib/api.ts
├── lib/hooks.ts
└── components/layout/Sidebar.tsx
```

---

## 🚀 Следующие шаги

1. **Ревью плана** — подтвердить структуру
2. **Фаза 1** — начать с backend моделей
3. **Постепенная имплементация** — по фазам с тестированием

---

*Документ создан: 2025-12-31*
