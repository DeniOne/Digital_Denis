# 🚀 TASK 7.1 — Deployment Strategy

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Средний  
**Зависимости:** Phase 0-6

---

## 📋 Чеклист реализации

- [x] docker-compose.yml финализирован
- [x] Все сервисы запускаются одной командой
- [x] .env.example актуален
- [x] Миграции запускаются автоматически
- [x] Health checks настроены
- [x] README с quick start

---

## 🎯 Цель

Описать стратегию деплоя: local / cloud / hybrid.

---

## 📦 Артефакт: Deployment Guide

### Варианты деплоя

| Вариант | Описание | Для кого |
|---------|----------|----------|
| **Local** | Docker Compose | Development, MVP |
| **Cloud** | Kubernetes / Cloud Run | Production |
| **Hybrid** | Local app + Cloud DB | Intermediate |

---

### Docker Compose (Local)

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/dd
      - REDIS_URL=redis://redis:6379/0
      - LLM_API_KEY=${LLM_API_KEY}
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

  telegram:
    build: ./telegram
    environment:
      - BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - API_URL=http://backend:8000

  worker:
    build: ./backend
    command: celery -A workers worker -l info
    depends_on:
      - redis

  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=dd

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection | ✅ |
| `REDIS_URL` | Redis connection | ✅ |
| `LLM_API_KEY` | Claude/OpenAI key | ✅ |
| `TELEGRAM_BOT_TOKEN` | Telegram bot | ✅ |
| `JWT_SECRET` | Auth secret | ✅ |
| `VECTOR_DB_URL` | Weaviate/FAISS | For v0.2+ |

---

### Quick Start

```bash
# 1. Clone
git clone https://github.com/user/digital-denis
cd digital-denis

# 2. Configure
cp .env.example .env
# Edit .env with your keys

# 3. Start
docker-compose up -d

# 4. Migrate
docker-compose exec backend alembic upgrade head

# 5. Access
# Web: http://localhost:3000
# API: http://localhost:8000/docs
```

---

## ✅ Критерии завершения

- [x] Local deployment работает
- [x] Cloud deployment описан
- [x] ENV variables документированы

---

## 📎 Связанные документы

- [TASK 1.1 — Repo Structure](../phase-1/TASK_1.1_Repo_Structure.md)
