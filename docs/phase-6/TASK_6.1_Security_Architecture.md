# 🔒 TASK 6.1 — Security & Access Control

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Высокий  
**Зависимости:** TASK 4.1

---

## 📋 Чеклист реализации

- [x] Реализовать JWT auth (backend/core/auth.py)
- [x] Telegram OAuth интеграция
- [x] Middleware для security headers
- [x] CORS настроен
- [x] Шифрование данных at rest
- [x] Все endpoints защищены
- [x] Security audit пройден

---

## 🎯 Цель

Спроектировать безопасность: auth, роли, доступ к памяти.

---

## 📦 Артефакт: Security Architecture Doc

### Authentication

| Метод | Описание | Use Case |
|-------|----------|----------|
| **JWT** | Bearer token | API access |
| **Telegram OAuth** | Через Telegram Login | Initial auth |
| **API Key** | Static key | Service-to-service |

```python
# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY = 24 * 60 * 60  # 24 hours

# Token payload
{
    "sub": "user_id",
    "exp": 1705334400,
    "iat": 1705248000,
    "scope": "owner"
}
```

---

### Roles & Permissions

| Роль | Описание | Scope |
|------|----------|-------|
| **Owner** | Владелец системы | Full access |
| **Viewer** | Только чтение | Read-only |
| **API** | Программный доступ | Limited endpoints |

### Access Control Matrix

| Resource | Owner | Viewer | API |
|----------|-------|--------|-----|
| Memory (read) | ✅ | ✅ | ✅ |
| Memory (write) | ✅ | ❌ | ❌ |
| Memory (delete) | ✅ | ❌ | ❌ |
| Topics | ✅ | ✅ | ✅ |
| Graph | ✅ | ✅ | ✅ |
| Anomalies | ✅ | ✅ | ❌ |
| Settings | ✅ | ❌ | ❌ |
| Send message | ✅ | ❌ | ❌ |

---

### Data Protection

| Данные | Уровень | Шифрование |
|--------|---------|------------|
| Memory content | High | AES-256 at rest |
| User profile | High | AES-256 at rest |
| Session data | Medium | TLS in transit |
| API keys | Critical | Hashed (bcrypt) |

---

### Security Headers

```python
# FastAPI middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://digital-denis.app"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization"],
)

# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

---

## ✅ Критерии завершения

- [x] Auth mechanisms определены
- [x] Роли и permissions описаны
- [x] Data protection спроектирован
- [x] Access control matrix готова

---

## 📎 Связанные документы

- [TASK 4.1 — API Contracts](../phase-4/TASK_4.1_API_Contracts.md)
- [TASK 6.2 — Observability](./TASK_6.2_Observability.md)
