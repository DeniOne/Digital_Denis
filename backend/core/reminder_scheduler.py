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
        from memory.schedule_models import ScheduleItem, ItemType, ItemStatus
        from memory.models import User
        from sqlalchemy import select, and_
        import pytz
        
        moscow_tz = pytz.timezone("Europe/Moscow")
        now = datetime.now(moscow_tz)
        
        async with async_session_maker() as db:
            # Find reminders that are due (within the last 5 minutes to catch any missed ones)
            query = select(ScheduleItem, User).join(
                User, ScheduleItem.user_id == User.id
            ).where(
                and_(
                    ScheduleItem.item_type == ItemType.REMINDER,
                    ScheduleItem.status == ItemStatus.PENDING,
                    ScheduleItem.start_at <= now,
                    ScheduleItem.start_at >= now - timedelta(minutes=5),
                )
            )
            
            result = await db.execute(query)
            items = result.all()
            
            if not items:
                return
            
            logger.info("pending_reminders_found", count=len(items))
            
            for item, user in items:
                if user.telegram_id:
                    success = await self._send_telegram_notification(
                        telegram_id=user.telegram_id,
                        title=item.title,
                        remind_at=item.start_at,
                        item_id=str(item.id),
                    )
                    
                    if success:
                        # Mark as completed
                        item.status = ItemStatus.COMPLETED
                        logger.info(
                            "reminder_sent",
                            item_id=str(item.id),
                            telegram_id=user.telegram_id,
                        )
                    else:
                        logger.warning(
                            "reminder_send_failed",
                            item_id=str(item.id),
                            telegram_id=user.telegram_id,
                        )
                else:
                    # No telegram_id, mark as completed anyway
                    item.status = ItemStatus.COMPLETED
                    logger.warning(
                        "reminder_no_telegram",
                        item_id=str(item.id),
                        user_id=str(user.id),
                    )
            
            await db.commit()

    
    async def _send_telegram_notification(
        self,
        telegram_id: int,
        title: str,
        remind_at: datetime,
        item_id: str,
    ) -> bool:
        """Send reminder notification via Telegram."""
        try:
            bot_token = settings.telegram_bot_token
            if not bot_token:
                logger.error("telegram_bot_token_not_configured")
                return False
            
            # Format message
            time_str = remind_at.strftime("%H:%M")
            message = f"🔔 **Напоминание**\n\n{title}\n⏰ {time_str}"
            
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
