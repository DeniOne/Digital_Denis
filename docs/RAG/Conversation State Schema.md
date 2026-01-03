Назначение

Conversation State (CS) — это явное состояние мышления диалога, используемое как первичный источник контекста для LLM.
CS не является историей сообщений и не является долговременной памятью.

1.1. Основная структура (JSON)
{
  "conversation_id": "uuid",
  "topic": "string | null",
  "goal": "string | null",
  "current_step": "string | null",
  "intent": "string | null",

  "active_entities": ["string"],
  "active_objects": ["string"],

  "assumptions": ["string"],
  "constraints": ["string"],

  "decisions_made": [
    {
      "id": "uuid",
      "summary": "string",
      "timestamp": "ISO-8601"
    }
  ],

  "open_questions": ["string"],
  "unresolved_points": ["string"],

  "confidence_level": "high | medium | low | unknown",

  "last_updated": "ISO-8601",
  "ttl_hours": 48
}

1.2. Поля и правила
topic

О чём сейчас диалог

Не меняется без явного сигнала

Пример: "RAG 2.0 architecture"

goal

Зачем идёт диалог

Пример: "Eliminate context loss in Telegram"

current_step

Стадия рассуждения

Примеры:

"problem analysis"

"root cause identified"

"solution design"

"implementation planning"

intent

Определяется интент-классификатором

Пример: "analysis", "decision_request"

active_entities / active_objects

Сущности, к которым относятся слова типа «это», «он», «тут»

Пример:

["Conversation State", "Redis", "Telegram Adapter"]

assumptions

Неявные допущения пользователя или системы

constraints

Явные ограничения:

«не упрощать»

«backend-first»

«без костылей»

decisions_made

Используется для:

предотвращения повторных обсуждений

фиксации переходов к Long-Term Memory

open_questions / unresolved_points

Критично для длинных диалогов в Telegram

1.3. Жизненный цикл

CS обновляется на каждом сообщении

TTL:

Telegram: 24–72 часа

При истечении TTL → CS сбрасывается с явным уведомлением LLM