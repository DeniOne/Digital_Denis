# Digital Denis — Personal Cognitive Operating System

**Digital Denis** — это персональная цифровая система для расширения когнитивных способностей, управления памятью и автоматизации задач.

---

## 🚀 Quick Start (Production / Docker)

Самый простой способ запустить систему — использовать Docker Compose.

### 1. Требования

- Docker & Docker Compose
- API Keys:
  - **OpenRouter** (или OpenAI/Anthropic) для LLM.
  - **Groq** (опционально) для распознавания голоса.
  - **Telegram Bot Token** для интерфейса (получить у @BotFather).

### 2. Установка

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/your-repo/digital-denis.git
    cd digital-denis
    ```

2.  **Настройте окружение:**
    Скопируйте пример файла конфигурации:
    ```bash
    cp .env.example .env
    ```
    Откройте `.env` и вставьте свои ключи (OPENROUTER_API_KEY, TELEGRAM_BOT_TOKEN и т.д.).
    
    > **Важно:** Генерируйте надежные ключи для `JWT_SECRET` и `ENCRYPTION_KEY`.
    > Для `ENCRYPTION_KEY` используйте 32 random bytes (base64 encoded).

3.  **Запустите сервисы:**
    ```bash
    docker-compose up -d --build
    ```

4.  **Примените миграции (первый запуск):**
    ```bash
    docker-compose exec backend alembic upgrade head
    ```

---

## 🛠 Локальная разработка

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

### Telegram Bot

```bash
cd telegram
python bot.py
```

---

## 🛡 Безопасность и Мониторинг

- **Swagger Documentation:** `http://localhost:8000/docs`
- **Prometheus Metrics:** `http://localhost:8000/metrics`
- **Health Checks:** `/health` endpoint

Система использует JWT для аутентификации и AES-256 для шифрования конфиденциальных данных в базе.
