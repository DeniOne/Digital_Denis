Целевая архитектура RAG 2.0

(Agentic + Typed Memory + Intent-aware + Temporal)

1.1. Концепция RAG 2.0

RAG 2.0 = не “поиск текста”, а управление знанием во времени и контексте.

Ключевые отличия от текущей схемы:

Память типизирована

Поиск зависит от интента

Контекст фреймится, а не просто подаётся

Есть метапамять и обратная связь (Kaizen)

1.2. Высокоуровневая архитектура
┌──────────────────────────────────────────────┐
│                  USER                        │
└──────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────┐
│             Core Orchestrator                │
│  - message normalization                     │
│  - intent detection                          │
│  - confidence mode                           │
└──────────────────────────────────────────────┘
        │                │
        │                ├───────────────┐
        ▼                ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Short-Term   │  │  Intent      │  │ Rules Engine │
│ Memory       │  │  Classifier  │  │ (Rules +     │
│ (Redis)      │  │              │  │ Principles)  │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │
        └──────┬─────────┘
               ▼
┌──────────────────────────────────────────────┐
│          Retrieval Engine (Hybrid)            │
│  - semantic search (pgvector)                 │
│  - full-text search (FTS)                     │
│  - type weighting                             │
│  - time decay                                 │
│  - conflict detection                        │
└──────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────┐
│        Context Assembler / Framer             │
│  - memory framing                             │
│  - confidence markers                        │
│  - ordering & limits                         │
└──────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────┐
│               LLM Core Agent                  │
│  - reasoning                                  │
│  - response generation                       │
│  - self-check                                 │
└──────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────┐
│           Kaizen & Meta-Memory Engine         │
│  - outcome tracking                          │
│  - memory usefulness scoring                 │
│  - trend detection                           │
└──────────────────────────────────────────────┘

1.3. Data Flow (пошагово)
Шаг 1. Ввод

Пользователь отправляет сообщение

Сообщение нормализуется (очистка, язык, длина)

Шаг 2. Определение интента

Примеры интентов:

decision_request

analysis

fact_check

reflection

planning

kaizen_review

Шаг 3. Retrieval (умный)

Используется формула:

final_score =
  semantic_similarity
  × memory_type_weight
  × intent_weight
  × time_decay

Шаг 4. Сборка контекста

Контекст не просто список, а структурированный фрейм:

Rules / Principles

Facts (high confidence)

Decisions

Reflections / Failures (если релевантно)

Conflicts (если есть)

Шаг 5. Генерация

LLM:

знает, чем можно опираться

знает, где неопределённость

обязан указывать конфликты

Шаг 6. Kaizen

Фиксируется: было ли это полезно

Используется ли память повторно

Улучшается ли качество решений