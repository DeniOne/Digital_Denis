# RAG 2.0 Production Deployment Guide

## Обновление на сервере (151.243.109.210)

### 1. Подключиться к серверу
```bash
ssh root@151.243.109.210
```

### 2. Перейти в директорию проекта
```bash
cd /path/to/digital-den  # уточнить путь
```

### 3. Обновить код из GitHub
```bash
git pull origin main
```

### 4. Применить миграции БД
```bash
cd backend
docker-compose exec backend alembic upgrade head
```

### 5. Перезапустить backend для подхвата новых компонентов
```bash
docker-compose restart backend
```

### 6. Обновить OpenRouter токен в .env (ВАЖНО!)
```bash
nano .env
# Добавить/обновить:
OPENROUTER_API_KEY=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
```

### 7. Еще раз перезапустить для подхвата токена
```bash
docker-compose restart backend
```

### 8. Проверить логи
```bash
docker-compose logs -f backend | grep "RAG 2.0"
```

## Что проверить после деплоя

1. **Веб-чат** - попробовать написать сообщение
2. **Telegram бот** - отправить сообщение боту
3. **Логи backend** - убедиться что нет ошибок:
   ```bash
   docker-compose logs backend --tail=100
   ```

## Новые таблицы в БД (проверить через psql)
```sql
\d conversation_states
\d memory_events
\d kaizen_metrics
```

## Rollback (если что-то пошло не так)
```bash
git reset --hard HEAD~1
docker-compose restart backend
```

## Примечания RAG 2.0

- ✅ Работает для Web и Telegram
- ✅ Graceful fallback на старый роутер при ошибках
- ✅ Поддержка анонимных пользователей
- ⚠️ Context truncated до 3000 символов (оптимизация)
- ⚠️ Требуется валидный OpenRouter API key
