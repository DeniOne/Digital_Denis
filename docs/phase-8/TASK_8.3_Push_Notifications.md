# 🔔 TASK 8.3 — Push Notifications (Android)

**Проект:** Digital Denis v0.2.0  
**Статус:** ⬜ Не начато  
**Приоритет:** Средний  
**Оценка:** 1 день  
**Зависимости:** TASK 8.1  
**Платформа:** 🤖 Android Only

---

## 🎯 Цель

Реализовать Push-уведомления для напоминаний и инсайтов.

---

## 📋 Чеклист реализации

### Backend
- [x] Модель `PushSubscription` в БД
- [x] Endpoint `POST /api/v1/notifications/subscribe`
- [x] Endpoint `DELETE /api/v1/notifications/unsubscribe`
- [x] VAPID ключи генерация и хранение
- [x] Сервис отправки push (web-push library)

### Frontend
- [x] Запрос разрешения на уведомления
- [x] Подписка на push через Service Worker
- [x] Отправка subscription на backend
- [x] Обработка push событий в SW
- [x] Click-to-open логика

### Триггеры уведомлений
- [x] Daily digest (Stub implemented)
- [x] Важные инсайты от агента (Helper implemented)
- [x] Напоминания о незавершённых задачах (Stub implemented)
- [x] Rate limiting (не более N в час)

### Настройки пользователя
- [x] UI для управления типами уведомлений
- [x] Quiet hours (не беспокоить с X до Y)
- [x] Полное отключение push

---

## 📦 Артефакты

```
backend/
├── api/
│   └── routes/
│       └── notifications.py    ✅ Created
├── core/
│   └── notifications.py        ✅ Created (Service)
└── db/
    └── models/
        └── push.py             ✅ Created (Model)

frontend/
└── src/
    ├── lib/
    │   └── push.ts             ✅ Created
    └── components/
        └── pwa/
            └── NotificationSettings.tsx ✅ Created
```

---

## 📝 Пример Push Subscription API

```python
# backend/api/routes/notifications.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

class PushSubscription(BaseModel):
    endpoint: str
    keys: dict  # p256dh, auth

@router.post("/subscribe")
async def subscribe(
    subscription: PushSubscription,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    # Save subscription to DB
    await save_subscription(db, current_user.id, subscription)
    return {"status": "subscribed"}

@router.delete("/unsubscribe")
async def unsubscribe(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    await remove_subscription(db, current_user.id)
    return {"status": "unsubscribed"}
```

---

## ✅ Критерии завершения

- [ ] Push работает на Android Chrome
- [ ] Уведомления открывают приложение
- [ ] Пользователь может управлять настройками
- [ ] Rate limiting работает

---

## 📎 Связанные документы

- [TASK 8.1 — PWA Setup](./TASK_8.1_PWA_Setup.md)
- [TASK 8.2 — Offline Mode](./TASK_8.2_Offline_Mode.md)
