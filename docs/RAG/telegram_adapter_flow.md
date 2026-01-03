2.1. Поток обработки (логический)
┌───────────────┐
│ Telegram User │
└───────┬───────┘
        ▼
┌────────────────────┐
│ Telegram Adapter   │
│ - normalize text   │
│ - detect reply     │
└───────┬────────────┘
        ▼
┌──────────────────────────┐
│ Load Conversation State  │
│ (by chat_id)             │
└───────┬──────────────────┘
        ▼
┌──────────────────────────┐
│ State Extractor           │
│ - update topic            │
│ - update goal             │
│ - update current_step     │
│ - resolve "this/it" refs  │
└───────┬──────────────────┘
        ▼
┌──────────────────────────┐
│ Intent Classifier         │
└───────┬──────────────────┘
        ▼
┌──────────────────────────┐
│ RAG 2.0 Retrieval         │
│ (intent + CS aware)       │
└───────┬──────────────────┘
        ▼
┌──────────────────────────┐
│ Context Assembler         │
│ PRIORITY ORDER:           │
│ 1. System Rules           │
│ 2. Conversation State     │
│ 3. Rules / Principles     │
│ 4. Long-Term Memory       │
│ 5. Last 3–5 messages      │
└───────┬──────────────────┘
        ▼
┌──────────────────────────┐
│ LLM Core Agent            │
└───────┬──────────────────┘
        ▼
┌──────────────────────────┐
│ Update Conversation State │
│ + Kaizen signals          │
└───────┬──────────────────┘
        ▼
┌───────────────┐
│ Telegram User │
└───────────────┘

2.2. Ключевое правило (жёсткое)

Если Conversation State отсутствует или пуст — LLM обязан запросить уточнение, а не угадывать.