"""
Digital Den — Embedded Reminder Scheduler
═══════════════════════════════════════════════════════════════════════════

Simple asyncio-based scheduler that runs within the FastAPI process.
Checks for pending reminders every minute and sends Telegram notifications.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
import httpx

from core.logging import get_logger
from core.config import settings

logger = get_logger(__name__)


class ReminderScheduler:
    """Embedded reminder scheduler using asyncio."""
    
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._check_interval = 60  # seconds
    
    async def start(self):
        """Start the reminder scheduler."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("reminder_scheduler_started", interval=self._check_interval)
        print("   📅 Reminder scheduler: started")
    
    async def stop(self):
        """Stop the reminder scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("reminder_scheduler_stopped")
    
    async def _run_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_pending_reminders()
            except Exception as e:
                logger.error("reminder_check_error", error=str(e))
            
            await asyncio.sleep(self._check_interval)
    
    async def _check_pending_reminders(self):
        """Check for pending reminders and send notifications."""
        from db.database import async_session_maker
        from memory.schedule_models import (
            ScheduleItem, ItemType, ItemStatus, 
            ReminderInstance, ReminderStatus, ReminderSchedule
        )
        from memory.models import User
        from sqlalchemy import select, and_, or_
        import pytz
        
        moscow_tz = pytz.timezone("Europe/Moscow")
        now = datetime.now(moscow_tz)
        
        async with async_session_maker() as db:
            # --- 1. Process Single Items (ScheduleItem) ---
            query = select(ScheduleItem, User).join(
                User, ScheduleItem.user_id == User.id
            ).where(
                and_(
                    ScheduleItem.status == ItemStatus.PENDING,
                    or_(
                        and_(ScheduleItem.start_at <= now, ScheduleItem.start_at >= now - timedelta(minutes=15)),
                        and_(ScheduleItem.due_at <= now, ScheduleItem.due_at >= now - timedelta(minutes=15)),
                    )
                )
            )
            
            result = await db.execute(query)
            items = result.all()
            
            for item, user in items:
                if user.telegram_id:
                    # Determine display time
                    display_time = item.start_at or item.due_at
                    prefix = "🔔"
                    if item.item_type == ItemType.TASK: prefix = "📅 Задача:"
                    elif item.item_type == ItemType.EVENT: prefix = "🗓 Встреча:"
                    
                    success = await self._send_telegram_notification(
                        telegram_id=user.telegram_id,
                        title=item.title,
                        remind_at=display_time,
                        item_id=str(item.id),
                        prefix=prefix
                    )
                    
                    if success:
                        item.status = ItemStatus.COMPLETED
                        logger.info("reminder_sent", item_id=str(item.id))
                else:
                    item.status = ItemStatus.COMPLETED

            # --- 2. Process Recurring Instances (ReminderInstance) ---
            query_inst = select(ReminderInstance, ReminderSchedule, User).join(
                ReminderSchedule, ReminderInstance.schedule_id == ReminderSchedule.id
            ).join(
                User, ReminderSchedule.user_id == User.id
            ).where(
                and_(
                    ReminderInstance.status == ReminderStatus.PENDING,
                    ReminderInstance.remind_at <= now,
                    ReminderInstance.remind_at >= now - timedelta(minutes=15),
                )
            )
            
            res_inst = await db.execute(query_inst)
            for inst, sched, user in res_inst.all():
                if user.telegram_id:
                    success = await self._send_telegram_notification(
                        telegram_id=user.telegram_id,
                        title=sched.title,
                        remind_at=inst.remind_at,
                        item_id=f"inst:{inst.id}",
                        prefix="💊 Напоминание:"
                    )
                    
                    if success:
                        inst.status = ReminderStatus.COMPLETED
                        logger.info("instance_sent", inst_id=str(inst.id))
                else:
                    inst.status = ReminderStatus.COMPLETED
            
            await db.commit()

    
    async def _send_telegram_notification(
        self,
        telegram_id: int,
        title: str,
        remind_at: datetime,
        item_id: str,
        prefix: str = "🔔 Напоминание:",
    ) -> bool:
        """Send reminder notification via Telegram."""
        try:
            bot_token = settings.telegram_bot_token
            if not bot_token:
                logger.error("telegram_bot_token_not_configured")
                return False
            
            # Format message
            time_str = remind_at.strftime("%H:%M")
            message = f"{prefix}\n\n{title}\n⏰ {time_str}"
            
            # Send via Telegram Bot API
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={
                        "chat_id": telegram_id,
                        "text": message,
                        "parse_mode": "Markdown",
                        "reply_markup": {
                            "inline_keyboard": [
                                [
                                    {"text": "✅ Готово", "callback_data": f"reminder:done:{item_id}"},
                                    {"text": "⏰ +15 мин", "callback_data": f"reminder:snooze:{item_id}"},
                                ]
                            ]
                        },
                    },
                    timeout=10.0,
                )
                
                if response.status_code == 200:
                    return True
                else:
                    logger.error(
                        "telegram_api_error",
                        status=response.status_code,
                        response=response.text,
                    )
                    return False
                    
        except Exception as e:
            logger.error("telegram_send_error", error=str(e))
            return False


# Global scheduler instance
reminder_scheduler = ReminderScheduler()
