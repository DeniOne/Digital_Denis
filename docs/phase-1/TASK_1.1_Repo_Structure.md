# 📁 TASK 1.1 — Repo & Project Structure

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Высокий  
**Зависимости:** TASK 0.2

---

## 📋 Чеклист реализации

- [x] Создать структуру папок backend/
- [x] Создать структуру папок frontend/
- [x] Создать структуру папок telegram/
- [x] Создать структуру папок ai/
- [x] Создать docker-compose.yml
- [x] Создать README.md (в корне проекта)
- [x] Git init + первый коммит

---

## 🎯 Цель

Спроектировать структуру репозитория Digital Denis (backend + frontend + docs).

---

## 📦 Артефакты

### 1. Repo Tree — Полная структура

```
digital-denis/
│
├── 📁 backend/                      # Python Backend (FastAPI)
│   ├── 📁 api/                      # REST API endpoints
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── messages.py          # POST /messages
│   │   │   ├── memory.py            # CRUD /memory
│   │   │   ├── topics.py            # GET /topics
│   │   │   ├── graph.py             # GET /graph
│   │   │   └── health.py            # GET /health, /anomalies
│   │   ├── schemas/                 # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── message.py
│   │   │   ├── memory.py
│   │   │   └── analytics.py
│   │   └── deps.py                  # Dependencies injection
│   │
│   ├── 📁 orchestrator/             # Core orchestration logic
│   │   ├── __init__.py
│   │   ├── router.py                # Request classification & routing
│   │   ├── context.py               # Context assembly
│   │   └── profile.py               # Digital Profile loader
│   │
│   ├── 📁 agents/                   # Agent implementations
│   │   ├── __init__.py
│   │   ├── base.py                  # Abstract base agent
│   │   ├── core_agent.py            # Core thinking partner
│   │   ├── analyst_agent.py         # Numbers & logic analysis
│   │   ├── operator_agent.py        # Ideas → Actions
│   │   ├── memory_agent.py          # Memory management
│   │   └── meta_analyst.py          # Async pattern analysis
│   │
│   ├── 📁 memory/                   # Memory layer
│   │   ├── __init__.py
│   │   ├── short_term.py            # Redis operations
│   │   ├── long_term.py             # PostgreSQL operations
│   │   ├── semantic.py              # Vector DB operations
│   │   └── models.py                # SQLAlchemy models
│   │
│   ├── 📁 analytics/                # CAL - Cognitive Analytics Layer
│   │   ├── __init__.py
│   │   ├── topics.py                # Topic Intelligence
│   │   ├── graphs.py                # Mind Map graphs
│   │   ├── logic.py                 # Decision analysis
│   │   └── anomalies.py             # Anomaly detection
│   │
│   ├── 📁 workers/                  # Background jobs (Celery/RQ)
│   │   ├── __init__.py
│   │   ├── tasks.py                 # Task definitions
│   │   └── scheduler.py             # Periodic tasks
│   │
│   ├── 📁 llm/                      # LLM providers
│   │   ├── __init__.py
│   │   ├── base.py                  # Abstract LLM interface
│   │   ├── claude.py                # Claude implementation
│   │   ├── openai.py                # GPT-4 implementation
│   │   └── prompts/                 # Prompt templates
│   │       ├── core_agent.md
│   │       ├── analyst_agent.md
│   │       └── ...
│   │
│   ├── 📁 core/                     # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py                # Settings from ENV
│   │   ├── logging.py               # Structured logging
│   │   └── exceptions.py            # Custom exceptions
│   │
│   ├── main.py                      # FastAPI app entry
│   ├── requirements.txt
│   └── Dockerfile
│
├── 📁 frontend/                     # Next.js Frontend
│   ├── 📁 app/                      # App Router (Next.js 14+)
│   │   ├── layout.tsx
│   │   ├── page.tsx                 # Dashboard
│   │   ├── memory/
│   │   │   └── page.tsx             # Memory Explorer
│   │   ├── topics/
│   │   │   └── page.tsx             # Topic Explorer
│   │   ├── mindmap/
│   │   │   └── page.tsx             # Mind Map View
│   │   └── health/
│   │       └── page.tsx             # Cognitive Health
│   │
│   ├── 📁 components/               # React components
│   │   ├── ui/                      # shadcn/ui components
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   └── Header.tsx
│   │   ├── memory/
│   │   │   ├── MemoryCard.tsx
│   │   │   └── MemoryList.tsx
│   │   ├── topics/
│   │   │   └── TopicTree.tsx
│   │   ├── graphs/
│   │   │   └── MindMapGraph.tsx
│   │   └── analytics/
│   │       ├── TrendChart.tsx
│   │       └── AnomalyAlert.tsx
│   │
│   ├── 📁 lib/                      # Utilities
│   │   ├── api.ts                   # API client
│   │   └── utils.ts
│   │
│   ├── 📁 hooks/                    # Custom React hooks
│   │   ├── useMemory.ts
│   │   └── useTopics.ts
│   │
│   ├── 📁 store/                    # State management
│   │   └── index.ts
│   │
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   └── Dockerfile
│
├── 📁 telegram/                     # Telegram Bot (отдельный сервис)
│   ├── bot.py                       # Main bot logic
│   ├── handlers.py                  # Message handlers
│   ├── requirements.txt
│   └── Dockerfile
│
├── 📁 db/                           # Database
│   ├── 📁 migrations/               # Alembic migrations
│   │   └── versions/
│   └── init.sql                     # Initial schema
│
├── 📁 ai/                           # AI Configuration
│   ├── 📁 profiles/                 # Digital Profiles
│   │   └── denis.yaml               # Main user profile
│   ├── 📁 prompts/                  # System prompts
│   │   ├── core_agent.md
│   │   ├── analyst_agent.md
│   │   ├── operator_agent.md
│   │   ├── memory_agent.md
│   │   └── meta_analyst.md
│   └── 📁 tools/                    # Agent tools definitions
│       └── tools.yaml
│
├── 📁 docs/                         # Documentation
│   ├── README.md                    # Docs index
│   ├── phase-0/
│   ├── phase-1/
│   ├── ... (as created)
│   └── ADR/                         # Architecture Decision Records
│       └── ADR-001-cal.md
│
├── 📁 scripts/                      # Utility scripts
│   ├── dev.sh                       # Start dev environment
│   ├── migrate.sh                   # Run migrations
│   └── seed.sh                      # Seed test data
│
├── docker-compose.yml               # Local development
├── docker-compose.prod.yml          # Production
├── .env.example                     # ENV template
├── .gitignore
├── README.md                        # Project README
└── Makefile                         # Common commands
```

---

### 2. Назначение ключевых папок

| Папка | Назначение | Владелец |
|-------|------------|----------|
| `backend/api/` | REST endpoints, HTTP layer | FastAPI Router |
| `backend/orchestrator/` | Центр принятия решений | Request Router |
| `backend/agents/` | Специализированные агенты | Agent implementations |
| `backend/memory/` | Все операции с памятью | Memory Layer |
| `backend/analytics/` | CAL — мета-анализ | Background workers |
| `backend/llm/` | Абстракция LLM providers | LLM Interface |
| `frontend/app/` | Страницы Control Plane | Next.js Router |
| `frontend/components/` | React UI компоненты | UI Layer |
| `telegram/` | Telegram Bot сервис | Dialog Interface |
| `ai/profiles/` | Digital Profile YAML | Configuration |
| `ai/prompts/` | System prompts агентов | Agent Behavior |
| `docs/` | Вся документация | Reference |

---

### 3. README Skeleton

```markdown
# 🧠 Digital Denis

Personal Cognitive Operating System

## 📌 What is this?

Digital Denis is a personal cognitive system (Digital Twin) designed to enhance 
the thinking of a specific person, not for universal assistance.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Local Development

```bash
# Clone repository
git clone https://github.com/yourname/digital-denis.git
cd digital-denis

# Copy environment
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# Run migrations
make migrate

# Access
# - Web UI: http://localhost:3000
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

## 🏗️ Architecture

See [docs/phase-0/TASK_0.1_Architecture_Overview.md](docs/phase-0/TASK_0.1_Architecture_Overview.md)

## 📚 Documentation

See [docs/README.md](docs/README.md)

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, Celery
- **Frontend:** Next.js, TypeScript, Tailwind, shadcn/ui
- **Data:** PostgreSQL, Redis, FAISS/Weaviate
- **AI:** Claude, GPT-4 (fallback)

## 📜 License

Private / Custom License (TBD)
```

---

## ✅ Критерии завершения

- [x] Структура соответствует архитектуре из TASK 0.1
- [x] Все слои имеют свои папки
- [x] Назначение каждой папки описано
- [x] README содержит базовую информацию

---

## 📎 Связанные документы

- [TASK 0.1 — Architecture Overview](../phase-0/TASK_0.1_Architecture_Overview.md)
- [TASK 0.2 — MVP Scope](../phase-0/TASK_0.2_MVP_Scope.md)
- [TASK 1.2 — Orchestrator Design](./TASK_1.2_Orchestrator_Design.md)
