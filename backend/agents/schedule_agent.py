"""
Digital Den - Schedule Agent
===========================================================================

Agent for managing schedules: events, tasks, reminders.
Parses user intent and creates schedule items.
"""

import json
import re
import pytz
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
from uuid import UUID

from agents.base import BaseAgent, AgentContext, AgentResponse
from core.schedule_service import (
    schedule_service, ReminderIntent, CycleIntent, ScheduleType
)
from memory.schedule_models import ItemType
from llm.base import LLMMessage
from llm.openrouter import openrouter
from core.logging import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Schedule Agent
# ═══════════════════════════════════════════════════════════════════════════

class ScheduleAgent(BaseAgent):
    """
    Agent for creating and managing schedules.
    
    Handles:
    - Events: "Поставь в расписание встречу..."
    - Tasks: "Добавь задачу..."
    - Reminders: "Напомни..."
    - Recurring: "Принимать таблетки каждый день..."
    """
    
    name = "schedule"
    description = "Schedule management: events, tasks, reminders"
    
    # ─────────────────────────────────────────────────────────────────────────
    # Main Processing
    # ─────────────────────────────────────────────────────────────────────────
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """Process schedule-related request."""
        
        try:
            # Extract intent from message (with history for relative references)
            intent = await self._extract_intent(context.user_message, context.history)
            
            if not intent:
                return AgentResponse(
                    content="Извини, не смог понять запрос о расписании. "
                            "Попробуй переформулировать, например:\n"
                            "• \"Напомни позвонить маме завтра в 15:00\"\n"
                            "• \"Отмени прошлое напоминание\"",
                    agent=self.name,
                    save_to_memory=False,
                )
            
            # Check if clarification needed
            if intent.get("needs_clarification"):
                return AgentResponse(
                    content=intent.get("clarification_question", "Уточни, пожалуйста, детали."),
                    agent=self.name,
                    save_to_memory=False,
                )
            
            # Execute action from intent
            result, extra_data = await self._execute_intent(intent, context)
            
            return AgentResponse(
                content=result,
                agent=self.name,
                save_to_memory=True,
                memory_type="task",
                memory_data=extra_data
            )
            
        except Exception as e:
            logger.error("schedule_agent_error", error=str(e))
            return AgentResponse(
                content=f"Произошла ошибка при создании записи в расписании: {str(e)}",
                agent=self.name,
                save_to_memory=False,
            )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Intent Extraction
    # ─────────────────────────────────────────────────────────────────────────
    
    async def _extract_intent(self, message: str, history: List[dict] = None) -> Optional[dict]:
        """
        Extract schedule intent from user message using LLM.
        """
        
        tz = pytz.timezone("Europe/Moscow")
        now = datetime.now(tz)
        today = now.date()
        
        # Format history for context (last 5 messages)
        history_str = ""
        if history:
            history_str = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in history[-5:]])
        
        prompt = f"""Ты — интеллектуальный ассистент расписания. Проанализируй сообщение и извлеки намерение.
Используй контекст предыдущих сообщений, чтобы понять относительные ссылки (например, "это напоминание", "прошлый раз", "про Рому").

Сегодня: {today.strftime('%Y-%m-%d')} ({today.strftime('%A')})
Текущее время: {now.strftime('%H:%M')}

Контекст последних сообщений:
{history_str}

Текущее сообщение пользователя:
"{message}"

Определи действие:
- "create" - создать новое событие/задачу/напоминание
- "cancel" - отменить/удалить существующее напоминание или задачу
- "list" - показать список дел

Верни JSON:
{{
    "action": "create|cancel|list",
    "item_type": "event|task|reminder|recurring",
    "title": "...", // О чем речь (например, 'День рождения Ромы')
    "date_reference": "...", // Упоминаемая дата, если есть (например, '16 мая')
    
    // Для action=create (ISO format):
    "start_at": "2025-01-05T14:00:00",
    "end_at": "2025-01-05T15:00:00",
    "duration_minutes": 60,
    "due_at": "2025-01-05T18:00:00",
    "schedule_type": "daily|weekly|monthly|yearly|interval",
    "times_of_day": ["08:00"],
    "start_date": "2025-05-16",
    "end_date": "2026-05-16",
    
    // Для сложных циклов (например, '5 дней приема, 30 дней перерыв'):
    "cycle": {{
        "active_days": 5,
        "pause_days": 30,
        "total_cycles": null // если указано количество курсов
    }},
    
    "needs_clarification": false,
    "clarification_question": null
}}

Правила:
1. Если не указано время - используй 08:00:00 (например, "2025-01-05T08:00:00")
2. "Завтра" = {(today + timedelta(days=1)).strftime('%Y-%m-%d')}
3. "Каждый год", "день рождения", "ежегодно" → schedule_type: "yearly"
4. "Каждый каждый месяц" → schedule_type: "monthly"
5. КРИТИЧЕСКИ ВАЖНО: При создании дня рождения ("день рождения 16 мая"), установи "start_date" именно на эту дату (например, "2025-05-16"), а не на сегодня.
6. Для КОРРЕКТНОЙ ОТМЕНЫ: если пользователь говорит "отмени его", посмотри в контексте, о каком последнем деле/напоминании шла речь, и заполни "title" и "item_type" соответственно.
7. СЛОЖНЫЕ ЦИКЛЫ: Если пользователь описывает курс (например, "5 дней через 30"), обязательно заполни объект "cycle". "active_days" - дни приема, "pause_days" - дни отдыха.

Верни ТОЛЬКО JSON, без объяснений:"""


        try:
            response = await openrouter.complete(
                messages=[LLMMessage(role="user", content=prompt)],
                max_tokens=1000,
                temperature=0.1,
            )
            
            # Extract JSON from response
            content = response.content.strip()
            
            # More robust JSON extraction: find the first '{' and last '}'
            match = re.search(r"(\{.*\})", content, re.DOTALL)
            if match:
                content = match.group(1)
            
            intent = json.loads(content)
            
            logger.info(
                "intent_extracted", 
                item_type=intent.get("item_type"),
                title=intent.get("title"),
                start_at=intent.get("start_at"),
                due_at=intent.get("due_at"),
                timezone=intent.get("timezone")
            )
            return intent
            
        except json.JSONDecodeError as e:
            logger.error("intent_parse_error", error=str(e), response=response.content[:500] if 'response' in locals() else "No response")
            return None
        except Exception as e:
            logger.error("intent_extraction_error", error=str(e))
            return None
    
    # ─────────────────────────────────────────────────────────────────────────
    # Intent Execution
    # =========================================================================
    
    async def _execute_intent(self, intent: dict, context: AgentContext) -> tuple[str, dict]:
        """Execute schedule action from parsed intent."""
        
        action = intent.get("action", "create")
        
        if action == "create":
            return await self._create_from_intent(intent, context)
        elif action == "cancel":
            return await self._cancel_from_intent(intent, context)
        elif action == "list":
            return "Я скоро научусь показывать список всех дел! А пока посмотри их в Календаре в Web-интерфейсе.", {}
        else:
            return f"⚠️ Действие '{action}' пока не поддерживается.", {}

    async def _create_from_intent(self, intent: dict, context: AgentContext) -> tuple[str, dict]:
        """Create schedule item from parsed intent."""
        
        item_type = intent.get("item_type", "reminder")
        title = intent.get("title", "Напоминание")
        
        # Get DB session from context (needs to be passed)
        db = context.db if hasattr(context, 'db') else None
        user_id = context.user_id if hasattr(context, 'user_id') else None
        
        if not db or not user_id:
            return "⚠️ Не удалось сохранить: нет подключения к БД.", {}
        
        try:
            if item_type == "event":
                start_at = self._parse_datetime(intent.get("start_at"))
                end_at = self._parse_datetime(intent.get("end_at"))
                duration = intent.get("duration_minutes", 60)
                
                item = await schedule_service.create_event(
                    db=db,
                    user_id=user_id,
                    title=title,
                    start_at=start_at,
                    end_at=end_at,
                    duration_minutes=duration,
                    description=intent.get("description"),
                    category=intent.get("category", "general"),
                    remind_before_minutes=intent.get("remind_before_minutes", 15),
                )
                
                return (
                    f"✅ **Встреча добавлена в расписание**\n\n"
                    f"📌 {title}\n"
                    f"📅 {start_at.astimezone(pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y')}\n"
                    f"🕐 {start_at.astimezone(pytz.timezone('Europe/Moscow')).strftime('%H:%M')} — {end_at.astimezone(pytz.timezone('Europe/Moscow')).strftime('%H:%M') if end_at else f'+{duration} мин'}\n"
                    f"🔔 Напомню за {intent.get('remind_before_minutes', 15)} мин",
                    {"item_id": str(item.id), "item_type": "event"}
                )
            
            elif item_type == "task":
                due_at = self._parse_datetime(intent.get("due_at"))
                
                item = await schedule_service.create_task(
                    db=db,
                    user_id=user_id,
                    title=title,
                    due_at=due_at,
                    description=intent.get("description"),
                    category=intent.get("category", "general"),
                    remind_before_minutes=intent.get("remind_before_minutes", 15),
                )
                
                return (
                    f"✅ **Задача добавлена**\n\n"
                    f"📌 {title}\n"
                    f"⏰ Дедлайн: {due_at.astimezone(pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y %H:%M')}\n"
                    f"🔔 Напомню за {intent.get('remind_before_minutes', 15)} мин",
                    {"item_id": str(item.id), "item_type": "task"}
                )
            
            elif item_type == "reminder":
                remind_at = self._parse_datetime(intent.get("start_at"))
                
                item = await schedule_service.create_reminder(
                    db=db,
                    user_id=user_id,
                    title=title,
                    remind_at=remind_at,
                    description=intent.get("description"),
                    category=intent.get("category", "general"),
                )
                
                return (
                    f"✅ **Напоминание создано**\n\n"
                    f"📌 {title}\n"
                    f"🔔 {remind_at.astimezone(pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y в %H:%M')}",
                    {"item_id": str(item.id), "item_type": "reminder"}
                )
            
            elif item_type == "recurring":
                # Build ReminderIntent
                cycle = None
                if intent.get("cycle"):
                    cycle = CycleIntent(
                        active_days=intent["cycle"].get("active_days", 1),
                        pause_days=intent["cycle"].get("pause_days", 0),
                        total_cycles=intent["cycle"].get("total_cycles"),
                    )
                
                schedule_type = ScheduleType.DAILY
                if intent.get("schedule_type") == "weekly":
                    schedule_type = ScheduleType.WEEKLY
                elif intent.get("schedule_type") == "monthly":
                    schedule_type = ScheduleType.MONTHLY
                elif intent.get("schedule_type") == "yearly":
                    schedule_type = ScheduleType.YEARLY
                elif intent.get("schedule_type") == "interval":
                    schedule_type = ScheduleType.INTERVAL
                
                reminder_intent = ReminderIntent(
                    title=title,
                    description=intent.get("description"),
                    category=intent.get("category", "health"),
                    schedule_type=schedule_type,
                    times_of_day=intent.get("times_of_day", []),
                    days_of_week=intent.get("days_of_week", []),
                    start_date=self._parse_date(intent.get("start_date")),
                    end_date=self._parse_date(intent.get("end_date")),
                    cycle=cycle,
                    timezone=intent.get("timezone", "Europe/Moscow"),
                    remind_before_minutes=intent.get("remind_before_minutes", 0),
                )
                
                schedule = await schedule_service.create_recurring(
                    db=db,
                    user_id=user_id,
                    intent=reminder_intent,
                )
                
                # Build response
                times = ", ".join(reminder_intent.times_of_day) if reminder_intent.times_of_day else "не указано"
                
                response = (
                    f"✅ **Повторяющееся напоминание создано**\n\n"
                    f"📌 {title}\n"
                    f"⏰ Время: {times}\n"
                )
                
                if cycle:
                    response += f"🔄 Цикл: {cycle.active_days} дн. приём, {cycle.pause_days} дн. перерыв\n"
                    if cycle.total_cycles:
                        response += f"📊 Всего циклов: {cycle.total_cycles}\n"
                
                if reminder_intent.end_date:
                    response += f"📅 До: {reminder_intent.end_date.strftime('%d.%m.%Y')}\n"
                
                return response, {"item_id": str(schedule.id), "item_type": "recurring"}
            
            else:
                return "⚠️ Неизвестный тип записи", {}
                
        except Exception as e:
            logger.error("create_from_intent_error", error=str(e), intent=intent)
            return f"⚠️ Ошибка создания: {str(e)}", {}

    async def _cancel_from_intent(self, intent: dict, context: AgentContext) -> tuple[str, dict]:
        """Cancel schedule item based on intent."""
        
        db = context.db
        user_id = context.user_id
        title = intent.get("title")
        
        try:
            # 1. Find candidate items
            candidates = await schedule_service.find_active_items(
                db=db,
                user_id=user_id,
                query=title
            )
            
            if not candidates:
                return f"🔍 Я не нашёл активных напоминаний или задач '{title or 'с таким названием'}', которые можно отменить.", {}
            
            # 2. If title matches exactly or only one item found
            target = None
            if len(candidates) == 1:
                target = candidates[0]
            else:
                # Try to find best match among multiple
                if title:
                    for c in candidates:
                        if title.lower() in c['title'].lower():
                            target = c
                            break
                
            if not target:
                items_str = "\n".join([f"• {c['title']}" for c in candidates])
                return (
                    f"🤔 Нашёл несколько похожих записей. Какую именно отменить?\n\n{items_str}",
                    {"candidates": [str(c['id']) for c in candidates]}
                )
            
            # 3. Perform cancellation
            success = await schedule_service.cancel_anything(db, user_id, target['id'])
            
            if success:
                return f"✅ Отменил: **{target['title']}**", {"cancelled_id": str(target['id'])}
            else:
                return f"❌ Не удалось отменить '{target['title']}'. Попробуй позже.", {}
                
        except Exception as e:
            logger.error("cancel_from_intent_error", error=str(e), intent=intent)
            return f"⚠️ Ошибка при отмене: {str(e)}", {}
    
    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # =========================================================================
    
    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """Parse datetime from ISO string with timezone safety."""
        if not value:
            return None
        try:
            # Replace common issues
            dt_str = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(dt_str)
            
            # If naive, assume Moscow (as requested by bot context)
            if dt.tzinfo is None:
                tz = pytz.timezone("Europe/Moscow")
                dt = tz.localize(dt)
            
            logger.debug("datetime_parsed", original=value, parsed=dt.isoformat())
            return dt
        except Exception as e:
            logger.error("datetime_parse_error", error=str(e), value=value)
            return None
    
    def _parse_date(self, value: Optional[str]) -> Optional[date]:
        """Parse date from string."""
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except:
            return None


# Global instance
schedule_agent = ScheduleAgent()
