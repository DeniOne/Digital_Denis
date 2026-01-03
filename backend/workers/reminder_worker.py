"""
Digital Den — Reminder Worker
═══════════════════════════════════════════════════════════════════════════

Celery tasks for processing and sending reminders.
"""

import os
import asyncio
from datetime import datetime, timedelta

from celery import shared_task
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

# Use the main app from tasks or cal_tasks depending on structure
# Based on tasks.py, 'app' is the Celery instance.
from workers.tasks import app as celery
from db.database import async_session
from memory.schedule_models import (
    ReminderInstance, ReminderSchedule, NotificationLog,
    ReminderStatus
)
from memory.models import User
from core.notifications import send_notification_to_user
from core.email_service import email_service
from core.schedule_service import ReminderGenerator
from core.logging import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Periodic Tasks Setup
# ═══════════════════════════════════════════════════════════════════════════

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks for reminders."""
    
    # Check pending reminders every minute
    sender.add_periodic_task(
        60.0,
        process_pending_reminders.s(),
        name="Process pending reminders"
    )
    
    # Retry unconfirmed reminders every 15 minutes
    sender.add_periodic_task(
        900.0,
        retry_unconfirmed_reminders.s(),
        name="Retry unconfirmed reminders"
    )
    
    # Generate upcoming instances daily at 3 AM
    sender.add_periodic_task(
        86400.0,
        generate_upcoming_instances.s(),
        name="Generate upcoming reminder instances"
    )
    
    # Sync Google Calendar every 15 minutes
    sender.add_periodic_task(
        900.0,
        sync_google_calendar_task.s(),
        name="Sync Google Calendar"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Main Tasks
# ═══════════════════════════════════════════════════════════════════════════

@shared_task(name="reminders.process_pending")
def process_pending_reminders():
    """Find and send all pending reminders that are due."""
    asyncio.run(_process_pending())
    

async def _process_pending():
    """Async implementation of processing pending reminders."""
    
    async with async_session() as db:
        now = datetime.utcnow()
        
        # Find pending instances where remind_at <= now
        result = await db.execute(
            select(ReminderInstance)
            .where(
                ReminderInstance.status == ReminderStatus.PENDING,
                ReminderInstance.remind_at <= now
            )
            .options(selectinload(ReminderInstance.schedule))
            .limit(100)  # Process in batches
        )
        
        instances = result.scalars().all()
        
        if not instances:
            return
        
        logger.info("processing_reminders", count=len(instances))
        
        for instance in instances:
            try:
                await _send_reminder(db, instance)
            except Exception as e:
                logger.error(
                    "reminder_send_error",
                    instance_id=str(instance.id),
                    error=str(e)
                )
        
        await db.commit()


async def _send_reminder(db, instance: ReminderInstance):
    """Send reminder through all configured channels."""
    
    schedule = instance.schedule
    if not schedule:
        return
    
    channels = schedule.channels or ["telegram", "push"]
    channels_used = []
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == schedule.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning("reminder_user_not_found", schedule_id=str(schedule.id))
        instance.status = ReminderStatus.MISSED
        return
    
    # Send via Telegram
    if "telegram" in channels and user.telegram_id:
        success = await _send_telegram_reminder(
            user.telegram_id,
            schedule.title,
            instance.remind_at,
            str(instance.id)
        )
        if success:
            channels_used.append("telegram")
            await _log_notification(db, instance.id, "telegram", "sent")
        else:
            await _log_notification(db, instance.id, "telegram", "failed")
    
    # Send via Push
    if "push" in channels:
        try:
            count = await send_notification_to_user(
                user_id=str(schedule.user_id),
                title=f"🔔 {schedule.title}",
                body=f"Время: {instance.remind_at.strftime('%H:%M')}",
                data={
                    "type": "reminder",
                    "instance_id": str(instance.id),
                    "schedule_id": str(schedule.id)
                },
                db=db
            )
            if count > 0:
                channels_used.append("push")
                await _log_notification(db, instance.id, "push", "sent")
        except Exception as e:
            logger.error("push_send_error", error=str(e))
            await _log_notification(db, instance.id, "push", "failed", str(e))

    # Send via Email
    if "email" in channels and user.email:
        try:
            success = await email_service.send_reminder(
                to_email=user.email,
                title=schedule.title,
                remind_at=instance.remind_at.strftime("%d.%m.%Y %H:%M"),
                description=schedule.description
            )
            if success:
                channels_used.append("email")
                await _log_notification(db, instance.id, "email", "sent")
            else:
                await _log_notification(db, instance.id, "email", "failed")
        except Exception as e:
            logger.error("email_send_error", error=str(e))
            await _log_notification(db, instance.id, "email", "failed", str(e))
    
    # Update instance
    instance.status = ReminderStatus.SENT
    instance.sent_at = datetime.utcnow()
    instance.channels_used = channels_used
    instance.next_retry_at = datetime.utcnow() + timedelta(minutes=15)
    
    logger.info(
        "reminder_sent",
        instance_id=str(instance.id),
        channels=channels_used
    )


async def _send_telegram_reminder(
    telegram_id: int,
    title: str,
    remind_at: datetime,
    instance_id: str
) -> bool:
    """Send reminder via Telegram with inline buttons."""
    
    try:
        from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
        
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("telegram_token_not_set")
            return False
        
        bot = Bot(token=token)
        
        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Выполнено", callback_data=f"reminder:done:{instance_id}"),
                InlineKeyboardButton("⏰ +15 мин", callback_data=f"reminder:snooze:{instance_id}"),
            ],
            [
                InlineKeyboardButton("❌ Пропустить", callback_data=f"reminder:skip:{instance_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format message
        text = (
            f"🔔 **Напоминание!**\n\n"
            f"📌 {title}\n"
            f"⏰ {remind_at.strftime('%d.%m.%Y %H:%M')}"
        )
        
        await bot.send_message(
            chat_id=telegram_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return True
        
    except Exception as e:
        logger.error("telegram_send_error", error=str(e), telegram_id=telegram_id)
        return False


async def _log_notification(
    db,
    instance_id,
    channel: str,
    status: str,
    error_message: str = None
):
    """Log notification attempt."""
    
    log = NotificationLog(
        instance_id=instance_id,
        channel=channel,
        status=status,
        error_message=error_message
    )
    db.add(log)


# ═══════════════════════════════════════════════════════════════════════════
# Retry Task
# ═══════════════════════════════════════════════════════════════════════════

@shared_task(name="reminders.retry_unconfirmed")
def retry_unconfirmed_reminders():
    """Retry reminders that were sent but not confirmed."""
    asyncio.run(_retry_unconfirmed())


async def _retry_unconfirmed():
    """Async implementation of retry logic."""
    
    async with async_session() as db:
        now = datetime.utcnow()
        
        # Find sent reminders that need retry
        result = await db.execute(
            select(ReminderInstance)
            .where(
                ReminderInstance.status == ReminderStatus.SENT,
                ReminderInstance.next_retry_at <= now,
                ReminderInstance.retry_count < 5  # Max 5 retries
            )
            .options(selectinload(ReminderInstance.schedule))
            .limit(50)
        )
        
        instances = result.scalars().all()
        
        if not instances:
            return
        
        logger.info("retrying_reminders", count=len(instances))
        
        for instance in instances:
            try:
                # Increment retry count
                instance.retry_count += 1
                instance.status = ReminderStatus.PENDING  # Reset to pending for resend
                
                await _send_reminder(db, instance)
                
            except Exception as e:
                logger.error(
                    "reminder_retry_error",
                    instance_id=str(instance.id),
                    error=str(e)
                )
        
        await db.commit()


# ═══════════════════════════════════════════════════════════════════════════
# Generation Task
# ═══════════════════════════════════════════════════════════════════════════

@shared_task(name="reminders.generate_upcoming")
def generate_upcoming_instances():
    """Generate reminder instances for the upcoming week."""
    asyncio.run(_generate_upcoming())


async def _generate_upcoming():
    """Async implementation of instance generation."""
    
    async with async_session() as db:
        # Find active schedules
        result = await db.execute(
            select(ReminderSchedule)
            .where(ReminderSchedule.is_active == True)
            .options(selectinload(ReminderSchedule.cycle))
        )
        
        schedules = result.scalars().all()
        
        if not schedules:
            return
        
        logger.info("generating_instances", schedules_count=len(schedules))
        
        total_generated = 0
        
        for schedule in schedules:
            try:
                generator = ReminderGenerator(schedule)
                instances = generator.generate(days_ahead=7)
                
                # Check for duplicates before adding
                for inst in instances:
                    existing = await db.execute(
                        select(ReminderInstance)
                        .where(
                            ReminderInstance.schedule_id == schedule.id,
                            ReminderInstance.remind_at == inst.remind_at
                        )
                    )
                    if not existing.scalar_one_or_none():
                        db.add(inst)
                        total_generated += 1
                        
            except Exception as e:
                logger.error(
                    "instance_generation_error",
                    schedule_id=str(schedule.id),
                    error=str(e)
                )
        
        await db.commit()
        
        logger.info("instances_generated", count=total_generated)


# ═══════════════════════════════════════════════════════════════════════════
# Manual Tasks
# ═══════════════════════════════════════════════════════════════════════════

@shared_task(name="reminders.confirm")
def confirm_reminder(instance_id: str):
    """Mark reminder as confirmed by user."""
    asyncio.run(_confirm_reminder(instance_id))


async def _confirm_reminder(instance_id: str):
    """Async implementation of confirmation."""
    
    from uuid import UUID
    
    async with async_session() as db:
        result = await db.execute(
            select(ReminderInstance).where(
                ReminderInstance.id == UUID(instance_id)
            )
        )
        instance = result.scalar_one_or_none()
        
        if instance:
            instance.status = ReminderStatus.CONFIRMED
            instance.confirmed_at = datetime.utcnow()
            await db.commit()
            
            logger.info("reminder_confirmed", instance_id=instance_id)


@shared_task(name="reminders.snooze")
def snooze_reminder(instance_id: str, minutes: int = 15):
    """Snooze reminder for specified minutes."""
    asyncio.run(_snooze_reminder(instance_id, minutes))


async def _snooze_reminder(instance_id: str, minutes: int):
    """Async implementation of snooze."""
    
    from uuid import UUID
    
    async with async_session() as db:
        result = await db.execute(
            select(ReminderInstance).where(
                ReminderInstance.id == UUID(instance_id)
            )
        )
        instance = result.scalar_one_or_none()
        
        if instance:
            instance.status = ReminderStatus.SNOOZED
            instance.snoozed_until = datetime.utcnow() + timedelta(minutes=minutes)
            instance.remind_at = instance.snoozed_until  # Update remind time
            instance.status = ReminderStatus.PENDING  # Will be picked up again
            await db.commit()
            
            logger.info("reminder_snoozed", instance_id=instance_id, minutes=minutes)


@shared_task(name="reminders.skip")
def skip_reminder(instance_id: str):
    """Mark reminder as skipped."""
    asyncio.run(_skip_reminder(instance_id))


async def _skip_reminder(instance_id: str):
    """Async implementation of skip."""
    
    from uuid import UUID
    
    async with async_session() as db:
        result = await db.execute(
            select(ReminderInstance).where(
                ReminderInstance.id == UUID(instance_id)
            )
        )
        instance = result.scalar_one_or_none()
        
        if instance:
            instance.status = ReminderStatus.MISSED
            await db.commit()
            
            logger.info("reminder_skipped", instance_id=instance_id)


# ═══════════════════════════════════════════════════════════════════════════
# Google Calendar Sync Tasks
# ═══════════════════════════════════════════════════════════════════════════

@shared_task(name="google.sync_all")
def sync_google_calendar_task():
    """Sync Google Calendar for all configured users."""
    asyncio.run(_sync_google_calendar())


async def _sync_google_calendar():
    """Async implementation of Google Calendar sync."""
    from memory.google_auth_models import GoogleCalendarConfig
    from core.google_calendar import GoogleCalendarService
    
    async with async_session() as db:
        # Find all users with Google Sync enabled
        result = await db.execute(
            select(GoogleCalendarConfig.user_id)
        )
        user_ids = [row[0] for row in result.fetchall()]
        
        if not user_ids:
            return
            
        logger.info("google_sync_batch_start", users_count=len(user_ids))
        
        service = GoogleCalendarService(db)
        for user_id in user_ids:
            try:
                # 1. Sync local things to Google
                await service.sync_to_google(user_id)
                
                # 2. Sync Google things to local
                await service.sync_from_google(user_id)
                
            except Exception as e:
                logger.error("google_sync_user_error", user_id=str(user_id), error=str(e))
        
        await db.commit()
