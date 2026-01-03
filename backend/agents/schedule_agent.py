"""
Digital Den — Schedule Agent
═══════════════════════════════════════════════════════════════════════════

Agent for managing schedules: events, tasks, reminders.
Parses user intent and creates schedule items.
"""

import json
import re
from datetime import datetime, date, timedelta
from typing import Optional
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
            # Extract intent from message
            intent = await self._extract_intent(context.user_message)
            
            if not intent:
                return AgentResponse(
                    content="Извини, не смог понять запрос о расписании. "
                            "Попробуй переформулировать, например:\n"
                            "• \"Напомни позвонить маме завтра в 15:00\"\n"
                            "• \"Поставь встречу с клиентом на понедельник в 10:00\"",
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
            
            # Create schedule item based on type
            result = await self._create_from_intent(intent, context)
            
            return AgentResponse(
                content=result,
                agent=self.name,
                save_to_memory=True,
                memory_type="task",
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
    
    async def _extract_intent(self, message: str) -> Optional[dict]:
        """
        Extract schedule intent from user message using LLM.
        """
        
        today = date.today()
        now = datetime.now()
        
        prompt = f"""Ты — парсер расписания. Извлеки информацию о событии/задаче/напоминании из сообщения.

Сегодня: {today.strftime('%Y-%m-%d')} ({today.strftime('%A')})
Текущее время: {now.strftime('%H:%M')}

Сообщение пользователя:
"{message}"

Определи тип:
- "event" — встреча, событие с началом и концом (длительностью)
- "task" — задача с дедлайном
- "reminder" — одноразовое напоминание
- "recurring" — повторяющееся напоминание

Верни JSON (без markdown!):
{{
    "action": "create",
    "item_type": "event|task|reminder|recurring",
    "title": "...",
    "description": null,
    "category": "general|work|personal|health",
    
    // Для event/reminder (ISO format):
    "start_at": "2025-01-05T14:00:00",
    "end_at": "2025-01-05T15:00:00",
    "duration_minutes": 60,
    
    // Для task:
    "due_at": "2025-01-05T18:00:00",
    
    // Для recurring:
    "schedule_type": "daily|weekly|interval",
    "times_of_day": ["08:00", "14:00", "20:00"],
    "days_of_week": [1, 2, 3, 4, 5],
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    
    // Цикл (если указан):
    "cycle": {{
        "active_days": 5,
        "pause_days": 30,
        "total_cycles": 12
    }},
    
    "timezone": "Europe/Moscow",
    "remind_before_minutes": 15,
    
    "needs_clarification": false,
    "clarification_question": null
}}

Правила:
1. Если не указано время — используй 08:00:00 по умолчанию (например, "2025-01-05T08:00:00")
2. "Завтра" = {(today + timedelta(days=1)).strftime('%Y-%m-%d')}
3. "Через час" = {(now + timedelta(hours=1)).strftime('%H:%M')}
4. Если не указана длительность встречи — по умолчанию 1 час
5. "Каждый день" → schedule_type: "daily"
6. "По будням" → days_of_week: [1,2,3,4,5]
7. "5 дней приём, 30 перерыв" → cycle

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
    # Create from Intent
    # ─────────────────────────────────────────────────────────────────────────
    
    async def _create_from_intent(self, intent: dict, context: AgentContext) -> str:
        """Create schedule item from parsed intent."""
        
        item_type = intent.get("item_type", "reminder")
        title = intent.get("title", "Напоминание")
        
        # Get DB session from context (needs to be passed)
        db = context.db if hasattr(context, 'db') else None
        user_id = context.user_id if hasattr(context, 'user_id') else None
        
        if not db or not user_id:
            return "⚠️ Не удалось сохранить: нет подключения к БД."
        
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
                    f"📅 {start_at.strftime('%d.%m.%Y')}\n"
                    f"🕐 {start_at.strftime('%H:%M')} — {end_at.strftime('%H:%M') if end_at else f'+{duration} мин'}\n"
                    f"🔔 Напомню за {intent.get('remind_before_minutes', 15)} мин"
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
                    f"⏰ Дедлайн: {due_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"🔔 Напомню за {intent.get('remind_before_minutes', 15)} мин"
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
                    f"🔔 {remind_at.strftime('%d.%m.%Y в %H:%M')}"
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
                
                return response
            
            else:
                return "⚠️ Неизвестный тип записи"
                
        except Exception as e:
            logger.error("create_from_intent_error", error=str(e), intent=intent)
            return f"⚠️ Ошибка создания: {str(e)}"
    
    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────
    
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
                import pytz
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
