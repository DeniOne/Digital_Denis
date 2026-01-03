# Инструкция по деплою Digital Den на VPS

Данная инструкция описывает процесс развертывания проекта на сервере Ubuntu с использованием Docker и Docker Compose.

## 1. Подготовка сервера

Убедитесь, что на сервере установлены:
- Docker (`docker --version`)
- Docker Compose (`docker-compose --version`)
- Git

## 2. Клонирование репозитория

```bash
mkdir -p /opt/digital-den
cd /opt/digital-den
git clone https://github.com/DeniOne/Digital_Denis.git .
```

## 3. Настройка окружения (.env)

Создайте файл `/opt/digital-den/.env` и заполните его:

```bash
# База данных
DATABASE_URL=postgresql://den:den_prod_2026@postgres:5432/digital_denis

# LLM Providers
OPENROUTER_API_KEY=your_key_here
GROQ_API_KEY=your_key_here

# Telegram
TELEGRAM_BOT_TOKEN=your_token_here
ALLOWED_TELEGRAM_IDS=your_id_here

# Продакшен настройки
FRONTEND_URL=http://your_vps_ip:3000
NEXT_PUBLIC_API_URL=http://your_vps_ip:8000/api/v1
```

> [!IMPORTANT]
> Замените `your_vps_ip` на реальный IP вашего сервера (например, `151.243.109.210`).

## 4. Сборка и запуск

### 4.1. Автоматическая подготовка docker-compose.yml

Для продакшена необходимо изменить PostgreSQL тэги и параметры подключения. Выполните:

```bash
sed -i 's/pgvector\/pgvector:pg15/pgvector\/pgvector:pg16/g' docker-compose.yml
sed -i 's/POSTGRES_USER: denis/POSTGRES_USER: den/g' docker-compose.yml
sed -i 's/POSTGRES_PASSWORD: denis_dev_2024/POSTGRES_PASSWORD: den_prod_2026/g' docker-compose.yml
sed -i 's/5434:5432/5432:5432/g' docker-compose.yml
```

### 4.2. Сборка образов

```bash
docker-compose build --no-cache
```

### 4.3. Запуск сервисов

```bash
docker-compose up -d
```

> [!NOTE]
> Если `docker-compose up` выдает ошибку `KeyError: 'ContainerConfig'`, запустите frontend напрямую через `docker run`:
> ```bash
> docker stop dd_frontend && docker rm dd_frontend
> docker run -d --name dd_frontend --network digital-den_default -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://your_vps_ip:8000/api/v1 -v /opt/digital-den/frontend:/app digital-den_frontend:latest npm run dev
> ```

## 5. Проверка статуса

```bash
# Проверить запущенные контейнеры
docker ps

# Проверить логи backend
docker logs dd_backend --tail 50

# Проверить логи frontend
docker logs dd_frontend --tail 50
```

## 6. Обновление проекта

При внесении изменений в код:

```bash
cd /opt/digital-den
git pull
docker-compose restart backend
# Если менялся frontend — требуется пересборка
docker-compose build frontend
docker-compose up -d frontend
```

---
## Типичные проблемы и решения

### Ошибка CORS
Убедитесь, что в `backend/main.py` в секции `CORSMiddleware` добавлен IP вашего сервера.

### Ошибка FileNotFoundError (Profile not found)
В `backend/core/config.py` путь `profile_path` должен быть `"ai/profiles/den.yaml"` для работы внутри Docker.

### Ошибка Hydration (Frontend)
Если браузерные расширения ломают верстку, в `Sidebar.tsx` должен быть добавлен атрибут `suppressHydrationWarning`.
