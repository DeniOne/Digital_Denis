# 📴 TASK 8.2 — Offline Mode (Android)

**Проект:** Digital Denis v0.2.0  
**Статус:** ⬜ Не начато  
**Приоритет:** Средний  
**Оценка:** 2 дня  
**Зависимости:** TASK 8.1  
**Платформа:** 🤖 Android Only

---

## 🎯 Цель

Обеспечить базовую работу приложения без интернета: создание черновиков и синхронизация при восстановлении связи.

---

## 📋 Чеклист реализации

### IndexedDB Storage
- [x] Настроить Dexie.js или idb для IndexedDB
- [x] Схема для хранения черновиков сообщений
- [x] Схема для очереди отправки
- [x] Миграции схемы

### Offline Queue
- [x] Перехват отправки сообщений при offline
- [x] Сохранение в очередь IndexedDB
- [x] Background sync при восстановлении
- [x] Retry logic с exponential backoff

### UI Indicators
- [x] Компонент `OfflineIndicator`
- [x] Toast при потере/восстановлении связи
- [x] Иконка статуса в header
- [x] Визуальная метка "pending" для неотправленных

### Sync Logic
- [x] Обработка `online`/`offline` событий
- [x] Background Sync API (если поддерживается)
- [x] Fallback на periodic sync
- [x] Conflict resolution (last-write-wins)

---

## 📦 Артефакты

```
frontend/
└── src/
    ├── lib/
    │   ├── db/
    │   │   ├── index.ts         ✅ IndexedDB setup
    │   │   └── schema.ts        ✅ DB schema
    │   └── sync/
    │       ├── queue.ts         # Offline queue
    │       └── manager.ts       ✅ Sync manager
    └── components/
        ├── pwa/
        │   └── OfflineIndicator.tsx ✅ Created
        └── PendingMessage.tsx
```

---

## 📝 Пример схемы IndexedDB

```typescript
// db/schema.ts
import Dexie from 'dexie';

class AppDB extends Dexie {
  drafts!: Table<Draft>;
  pendingMessages!: Table<PendingMessage>;
  
  constructor() {
    super('DigitalDenisDB');
    this.version(1).stores({
      drafts: '++id, content, createdAt',
      pendingMessages: '++id, content, sessionId, createdAt, status'
    });
  }
}

interface PendingMessage {
  id?: number;
  content: string;
  sessionId: string;
  createdAt: Date;
  status: 'pending' | 'sending' | 'failed';
  retryCount: number;
}
```

---

## ✅ Критерии завершения

- [ ] Сообщения сохраняются при offline
- [ ] Автоматическая отправка при online
- [ ] UI показывает статус подключения
- [ ] Нет потери данных при переключении

---

## 📎 Связанные документы

- [TASK 8.1 — PWA Setup](./TASK_8.1_PWA_Setup.md)
- [TASK 8.3 — Push Notifications](./TASK_8.3_Push_Notifications.md)
