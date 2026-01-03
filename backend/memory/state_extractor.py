"""
Digital Den — State Extractor Service
═══════════════════════════════════════════════════════════════════════════

AI-агент для обновления Conversation State.
НЕ отвечает пользователю, только обновляет состояние диалога.
"""

import json
from typing import Optional, List, Dict
from uuid import UUID

from llm.openrouter import openrouter


class StateExtractor:
    """
    AI-агент для инкрементального обновления Conversation State.
    
    Принципы:
    - Не удаляет информацию без причины
    - Не придумывает цель или тему
    - Обновляет только то, что явно изменилось
    - Разрешает анафоры ("это", "тут", "он") через active_entities
    """
    
    SYSTEM_PROMPT = """
Ты — Conversation State Extractor.

Твоя задача — поддерживать и обновлять структурированное состояние диалога, а НЕ отвечать пользователю.

## ВХОДНЫЕ ДАННЫЕ

Ты получаешь:
- previous_conversation_state (JSON или null)
- last_messages (3–5 последних реплик)
- current_message

## ТРЕБОВАНИЯ

✅ Не удаляй информацию без причины
✅ Не придумывай цель или тему — если неясно, оставь null
✅ Обновляй только то, что явно изменилось
✅ Разрешай анафоры ("это", "тут", "он") через active_entities

## ПРАВИЛА ОБНОВЛЕНИЯ

- Если тема не менялась → сохраняй active_topic
- Если пользователь меняет задачу → обнови goal
- Если принят вывод → добавь в decisions_made
- Если вопрос остался без ответа → добавь в open_questions

## ЗАПРЕТЫ

❌ Не отвечай пользователю
❌ Не добавляй комментарии вне JSON
❌ Не форматируй Markdown в выводе

## ВЫХОД

Верни ТОЛЬКО JSON обновлённого Conversation State в формате:
{
  "topic": "string | null",
  "goal": "string | null",
  "current_step": "string | null",
  "intent": "string | null",
  "active_entities": ["string"],
  "active_objects": ["string"],
  "assumptions": ["string"],
  "constraints": ["string"],
  "decisions_made": [
    {"id": "uuid", "summary": "string", "timestamp": "ISO-8601"}
  ],
  "open_questions": ["string"],
  "unresolved_points": ["string"],
  "confidence_level": "high | medium | low | unknown"
}
"""
    
    async def extract_state(
        self,
        previous_state: Optional[Dict],
        last_messages: List[Dict],
        current_message: str,
        user_id: UUID,
    ) -> Dict:
        """
        Обновляет Conversation State инкрементально.
        
        Args:
            previous_state: Предыдущее состояние (или None)
            last_messages: Последние 3-5 сообщений [{"role": "user|assistant", "content": "..."}]
            current_message: Текущее сообщение пользователя
            user_id: ID пользователя
            
        Returns:
            Dict с обновлённым состоянием
        """
        # 1. Подготовка контекста
        context = {
            "previous_state": previous_state if previous_state else {
                "topic": None,
                "goal": None,
                "current_step": None,
                "intent": None,
                "active_entities": [],
                "active_objects": [],
                "assumptions": [],
                "constraints": [],
                "decisions_made": [],
                "open_questions": [],
                "unresolved_points": [],
                "confidence_level": "unknown"
            },
            "last_messages": last_messages[-5:] if last_messages else [],
            "current_message": current_message,
        }
        
        # 2. Вызов LLM
        try:
            response = await openrouter.generate(
                system_prompt=self.SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": json.dumps(context, ensure_ascii=False, indent=2)
                    }
                ],
                model="anthropic/claude-3.5-sonnet",  # или gpt-4o-mini для скорости
                temperature=0.2,  # низкая температура для детерминизма
                max_tokens=1500,
            )
            
            # 3. Парсинг JSON
            content = response.get("content", "{}")
            
            # Попытка извлечь JSON из возможного markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            updated_state = json.loads(content)
            
            return updated_state
            
        except json.JSONDecodeError as e:
            print(f"State Extractor JSON parsing error: {e}")
            print(f"Response content: {content}")
            # Fallback: вернуть previous_state без изменений
            return previous_state if previous_state else {}
        
        except Exception as e:
            print(f"State Extractor error: {e}")
            return previous_state if previous_state else {}


# Global instance
state_extractor = StateExtractor()
