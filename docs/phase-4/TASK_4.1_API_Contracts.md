# 📡 TASK 4.1 — Backend API Contracts

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Высокий  
**Зависимости:** TASK 3.1, TASK 2.1

---

## 📋 Чеклист реализации

- [x] Создать backend/api/routes/messages.py
- [x] Создать backend/api/routes/memory.py
- [x] Создать backend/api/routes/topics.py
- [x] Создать backend/api/routes/graph.py
- [x] Создать backend/api/routes/health.py
- [x] Все endpoints документированы (OpenAPI)
- [x] Написать API тесты (pytest)

---

## 🎯 Цель

Описать REST API контракты между фронтом и бэкендом.

---

## 📦 Артефакт: OpenAPI Spec

### Base Configuration

```yaml
openapi: 3.0.3
info:
  title: Digital Denis API
  version: 1.0.0
  description: Personal Cognitive Operating System API

servers:
  - url: http://localhost:8000/api/v1
    description: Development
  - url: https://api.digital-denis.app/v1
    description: Production

security:
  - bearerAuth: []
```

---

### 1. Messages API

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/messages` | Отправить сообщение |
| GET | `/messages/session/{id}` | История сессии |

```yaml
/messages:
  post:
    summary: Send message to agent
    requestBody:
      content:
        application/json:
          schema:
            type: object
            required: [content]
            properties:
              content:
                type: string
              session_id:
                type: string
                format: uuid
              mode:
                type: string
                enum: [fast, deep, batch]
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                response:
                  type: string
                agent:
                  type: string
                memory_saved:
                  type: boolean
                session_id:
                  type: string
```

---

### 2. Memory API

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/memory` | Список items (paginated) |
| GET | `/memory/{id}` | Детали item |
| POST | `/memory/search` | Поиск по памяти |
| DELETE | `/memory/{id}` | Удалить (soft) |

```yaml
/memory:
  get:
    summary: List memory items
    parameters:
      - name: type
        in: query
        schema:
          type: string
          enum: [decision, insight, fact, all]
      - name: topic_id
        in: query
        schema:
          type: string
          format: uuid
      - name: limit
        in: query
        schema:
          type: integer
          default: 20
      - name: offset
        in: query
        schema:
          type: integer
          default: 0
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                items:
                  type: array
                  items:
                    $ref: '#/components/schemas/MemoryItem'
                total:
                  type: integer
```

---

### 3. Topics API

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/topics` | Список тем (flat) |
| GET | `/topics/tree` | Дерево тем |
| GET | `/topics/{id}/items` | Items по теме |
| GET | `/topics/trends` | Тренды тем |

---

### 4. Graph API

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/graph` | Данные графа |
| GET | `/graph/subgraph/{topic_id}` | Подграф по теме |

```yaml
/graph:
  get:
    summary: Get mind map graph
    parameters:
      - name: topic_id
        in: query
        schema:
          type: string
      - name: days
        in: query
        schema:
          type: integer
          default: 30
      - name: max_nodes
        in: query
        schema:
          type: integer
          default: 100
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                nodes:
                  type: array
                  items:
                    $ref: '#/components/schemas/GraphNode'
                edges:
                  type: array
                  items:
                    $ref: '#/components/schemas/GraphEdge'
```

---

### 5. Analytics API

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/analytics/anomalies` | Текущие аномалии |
| PATCH | `/analytics/anomalies/{id}` | Обновить статус |
| GET | `/analytics/health` | Cognitive health report |
| GET | `/analytics/decisions/{id}` | Анализ решения |

---

### 6. Components (Schemas)

```yaml
components:
  schemas:
    MemoryItem:
      type: object
      properties:
        id:
          type: string
          format: uuid
        type:
          type: string
          enum: [decision, insight, fact, thought]
        content:
          type: string
        summary:
          type: string
        confidence:
          type: number
        topics:
          type: array
          items:
            $ref: '#/components/schemas/TopicRef'
        created_at:
          type: string
          format: date-time
    
    TopicRef:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        confidence:
          type: number
    
    GraphNode:
      type: object
      properties:
        id:
          type: string
        label:
          type: string
        type:
          type: string
        size:
          type: number
        data:
          type: object
    
    GraphEdge:
      type: object
      properties:
        source:
          type: string
        target:
          type: string
        type:
          type: string
        weight:
          type: number
  
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

---

## ✅ Критерии завершения

- [x] Все endpoints описаны
- [x] Request/Response форматы определены
- [x] Аутентификация описана
- [x] Готово для OpenAPI 3.0

---

## 📎 Связанные документы

- [TASK 2.1 — Memory Layer Design](../phase-2/TASK_2.1_Memory_Layer_Design.md)
- [TASK 3.1 — CAL Architecture](../phase-3/TASK_3.1_CAL_Architecture.md)
