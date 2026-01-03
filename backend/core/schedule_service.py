"""
Digital Den — Schedule Service
═══════════════════════════════════════════════════════════════════════════

Service for managing schedules: events, tasks, reminders.
"""

import pytz
from datetime import datetime, date, timedelta
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from memory.schedule_models import (
    ScheduleItem, ReminderSchedule, ReminderCycle, ReminderInstance,
    ItemType, ItemStatus, ScheduleType, ReminderStatus
)
from core.logging import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Data Classes for Intent
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CycleIntent:
    """Cycle configuration for recurring reminders."""
    active_days: int
    pause_days: int
    total_cycles: Optional[int] = None


@dataclass
class ReminderIntent:
    """Intent extracted from user message for creating reminders."""
    title: str
    category: str = "general"
    description: Optional[str] = None
    
    # Type of schedule
    schedule_type: ScheduleType = ScheduleType.SINGLE
    
    # For single event/reminder
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    
    # For recurring
    times_of_day: List[str] = None  # ["08:00", "14:00", "20:00"]
    days_of_week: List[int] = None  # [1, 2, 3, 4, 5]
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Cycle
    cycle: Optional[CycleIntent] = None
    
    # Settings
    timezone: str = "Europe/Moscow"
    remind_before_minutes: int = 0
    channels: List[str] = None
    
    def __post_init__(self):
        if self.times_of_day is None:
            self.times_of_day = []
        if self.days_of_week is None:
            self.days_of_week = []
        if self.channels is None:
            self.channels = ["telegram", "push"]


# ═══════════════════════════════════════════════════════════════════════════
# Schedule Service
# ═══════════════════════════════════════════════════════════════════════════

class ScheduleService:
    """Service for managing user schedules."""
    
    # ─────────────────────────────────────────────────────────────────────────
    # Create Operations
    # ─────────────────────────────────────────────────────────────────────────
    
    async def create_event(
        self,
        db: AsyncSession,
        user_id: UUID,
        title: str,
        start_at: datetime,
        end_at: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        description: Optional[str] = None,
        category: str = "general",
        remind_before_minutes: int = 15,
        channels: List[str] = None,
        timezone: str = "Europe/Moscow",
    ) -> ScheduleItem:
        """Create an event (meeting, appointment)."""
        
        if end_at is None and duration_minutes:
            end_at = start_at + timedelta(minutes=duration_minutes)
        
        item = ScheduleItem(
            user_id=user_id,
            item_type=ItemType.EVENT,
            title=title,
            description=description,
            category=category,
            start_at=start_at,
            end_at=end_at,
            duration_minutes=duration_minutes,
            timezone=timezone,
            remind_before_minutes=remind_before_minutes,
            channels=channels or ["telegram", "push"],
            source="assistant",
        )
        
        db.add(item)
        await db.commit()
        await db.refresh(item)
        
        logger.info("event_created", item_id=str(item.id), title=title)
        return item
    
    async def create_task(
        self,
        db: AsyncSession,
        user_id: UUID,
        title: str,
        due_at: datetime,
        description: Optional[str] = None,
        category: str = "general",
        remind_before_minutes: int = 15,
        channels: List[str] = None,
        timezone: str = "Europe/Moscow",
    ) -> ScheduleItem:
        """Create a task with deadline."""
        
        item = ScheduleItem(
            user_id=user_id,
            item_type=ItemType.TASK,
            title=title,
            description=description,
            category=category,
            due_at=due_at,
            timezone=timezone,
            remind_before_minutes=remind_before_minutes,
            channels=channels or ["telegram", "push"],
            source="assistant",
        )
        
        db.add(item)
        await db.commit()
        await db.refresh(item)
        
        logger.info("task_created", item_id=str(item.id), title=title)
        return item
    
    async def create_reminder(
        self,
        db: AsyncSession,
        user_id: UUID,
        title: str,
        remind_at: datetime,
        description: Optional[str] = None,
        category: str = "general",
        channels: List[str] = None,
        timezone: str = "Europe/Moscow",
    ) -> ScheduleItem:
        """Create a one-time reminder."""
        
        item = ScheduleItem(
            user_id=user_id,
            item_type=ItemType.REMINDER,
            title=title,
            description=description,
            category=category,
            start_at=remind_at,
            timezone=timezone,
            remind_before_minutes=0,  # Remind exactly at time
            channels=channels or ["telegram", "push"],
            source="assistant",
        )
        
        db.add(item)
        await db.commit()
        await db.refresh(item)
        
        logger.info("reminder_created", item_id=str(item.id), title=title)
        return item
    
    async def create_recurring(
        self,
        db: AsyncSession,
        user_id: UUID,
        intent: ReminderIntent,
    ) -> ReminderSchedule:
        """Create a recurring reminder with optional cycles."""
        
        # Create schedule
        schedule = ReminderSchedule(
            user_id=user_id,
            title=intent.title,
            description=intent.description,
            category=intent.category,
            schedule_type=intent.schedule_type,
            times_of_day=intent.times_of_day,
            days_of_week=intent.days_of_week,
            start_date=intent.start_date or date.today(),
            end_date=intent.end_date,
            timezone=intent.timezone,
            remind_before_minutes=intent.remind_before_minutes,
            channels=intent.channels,
            is_active=True,
        )
        
        db.add(schedule)
        await db.flush()
        
        # Create cycle if needed
        if intent.cycle:
            cycle = ReminderCycle(
                schedule_id=schedule.id,
                active_days=intent.cycle.active_days,
                pause_days=intent.cycle.pause_days,
                total_cycles=intent.cycle.total_cycles,
                cycle_start_date=intent.start_date or date.today(),
                is_in_pause=False,
            )
            db.add(cycle)
        
        await db.flush()
        
        # Generate instances for next 7 days
        generator = ReminderGenerator(schedule)
        instances = generator.generate(days_ahead=7)
        
        for inst in instances:
            db.add(inst)
        
        await db.commit()
        await db.refresh(schedule)
        
        logger.info(
            "recurring_created",
            schedule_id=str(schedule.id),
            title=intent.title,
            instances_count=len(instances)
        )
        
        return schedule
    
    # ─────────────────────────────────────────────────────────────────────────
    # Read Operations
    # ─────────────────────────────────────────────────────────────────────────
    
    async def get_schedule(
        self,
        db: AsyncSession,
        user_id: UUID,
        date_from: date,
        date_to: date,
        include_completed: bool = False,
    ) -> List[ScheduleItem]:
        """Get schedule items for date range."""
        
        conditions = [
            ScheduleItem.user_id == user_id,
            or_(
                and_(ScheduleItem.start_at >= date_from, ScheduleItem.start_at < date_to),
                and_(ScheduleItem.due_at >= date_from, ScheduleItem.due_at < date_to),
            )
        ]
        
        if not include_completed:
            conditions.append(ScheduleItem.status.in_([ItemStatus.PENDING, ItemStatus.IN_PROGRESS]))
        
        result = await db.execute(
            select(ScheduleItem)
            .where(and_(*conditions))
            .order_by(ScheduleItem.start_at, ScheduleItem.due_at)
        )
        
        return result.scalars().all()
    
    async def get_today_schedule(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> List[ScheduleItem]:
        """Get today's schedule items."""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        return await self.get_schedule(db, user_id, today, tomorrow)
    
    async def get_pending_reminders(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> List[ReminderSchedule]:
        """Get active recurring reminders."""
        
        result = await db.execute(
            select(ReminderSchedule)
            .where(
                ReminderSchedule.user_id == user_id,
                ReminderSchedule.is_active == True
            )
            .options(selectinload(ReminderSchedule.cycle))
        )
        
        return result.scalars().all()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Update Operations
    # ─────────────────────────────────────────────────────────────────────────
    
    async def complete_item(
        self,
        db: AsyncSession,
        item_id: UUID,
        user_id: UUID,
    ) -> Optional[ScheduleItem]:
        """Mark item as completed."""
        
        result = await db.execute(
            select(ScheduleItem).where(
                ScheduleItem.id == item_id,
                ScheduleItem.user_id == user_id
            )
        )
        item = result.scalar_one_or_none()
        
        if item:
            item.status = ItemStatus.COMPLETED
            item.completed_at = datetime.now(pytz.UTC)
            await db.commit()
            logger.info("item_completed", item_id=str(item_id))
        
        return item
    
    async def skip_item(
        self,
        db: AsyncSession,
        item_id: UUID,
        user_id: UUID,
    ) -> Optional[ScheduleItem]:
        """Mark item as missed/skipped."""
        
        result = await db.execute(
            select(ScheduleItem).where(
                ScheduleItem.id == item_id,
                ScheduleItem.user_id == user_id
            )
        )
        item = result.scalar_one_or_none()
        
        if item:
            item.status = ItemStatus.MISSED
            await db.commit()
            logger.info("item_skipped", item_id=str(item_id))
        
        return item
    
    async def cancel_item(
        self,
        db: AsyncSession,
        item_id: UUID,
        user_id: UUID,
    ) -> Optional[ScheduleItem]:
        """Cancel an item."""
        
        result = await db.execute(
            select(ScheduleItem).where(
                ScheduleItem.id == item_id,
                ScheduleItem.user_id == user_id
            )
        )
        item = result.scalar_one_or_none()
        
        if item:
            item.status = ItemStatus.CANCELLED
            await db.commit()
            logger.info("item_cancelled", item_id=str(item_id))
        
        return item
    
    async def pause_schedule(
        self,
        db: AsyncSession,
        schedule_id: UUID,
        user_id: UUID,
    ) -> Optional[ReminderSchedule]:
        """Pause a recurring schedule."""
        
        result = await db.execute(
            select(ReminderSchedule).where(
                ReminderSchedule.id == schedule_id,
                ReminderSchedule.user_id == user_id
            )
        )
        schedule = result.scalar_one_or_none()
        
        if schedule:
            schedule.is_active = False
            await db.commit()
            logger.info("schedule_paused", schedule_id=str(schedule_id))
        
        return schedule


# ═══════════════════════════════════════════════════════════════════════════
# Reminder Generator
# ═══════════════════════════════════════════════════════════════════════════

class ReminderGenerator:
    """
    Generates ReminderInstance objects from ReminderSchedule.
    Handles cycles (active/pause days) and various schedule types.
    """
    
    def __init__(self, schedule: ReminderSchedule):
        self.schedule = schedule
        self.tz = pytz.timezone(schedule.timezone)
    
    def generate(self, days_ahead: int = 7) -> List[ReminderInstance]:
        """Generate instances for the next N days."""
        
        instances = []
        today = date.today()
        
        for day_offset in range(days_ahead):
            current_date = today + timedelta(days=day_offset)
            
            # Check date bounds
            if current_date < self.schedule.start_date:
                continue
            if self.schedule.end_date and current_date > self.schedule.end_date:
                break
            
            # Check if day is active (considering cycles)
            if not self._is_active_day(current_date):
                continue
            
            # Check day of week for weekly schedules
            if self.schedule.schedule_type == ScheduleType.WEEKLY:
                if current_date.isoweekday() not in (self.schedule.days_of_week or []):
                    continue
            
            # Check interval for interval schedules
            if self.schedule.schedule_type == ScheduleType.INTERVAL:
                days_since_start = (current_date - self.schedule.start_date).days
                if self.schedule.interval_days and days_since_start % self.schedule.interval_days != 0:
                    continue
            
            # Generate instances for each time of day
            for time_str in (self.schedule.times_of_day or []):
                remind_at = self._combine_date_time(current_date, time_str)
                
                # Skip past times
                if remind_at <= datetime.now(self.tz):
                    continue
                
                instances.append(ReminderInstance(
                    schedule_id=self.schedule.id,
                    remind_at=remind_at,
                    status=ReminderStatus.PENDING,
                ))
        
        return instances
    
    def _is_active_day(self, check_date: date) -> bool:
        """Check if date is an active day (not in pause period)."""
        
        cycle = self.schedule.cycle
        if not cycle:
            return True  # No cycle = always active
        
        # Calculate position in cycle
        days_since_start = (check_date - cycle.cycle_start_date).days
        if days_since_start < 0:
            return False
        
        cycle_length = cycle.active_days + cycle.pause_days
        position_in_cycle = days_since_start % cycle_length
        
        # Check if we've exceeded total cycles
        if cycle.total_cycles:
            current_cycle_num = days_since_start // cycle_length + 1
            if current_cycle_num > cycle.total_cycles:
                return False
        
        # Active days = [0, active_days)
        return position_in_cycle < cycle.active_days
    
    def _combine_date_time(self, d: date, time_str: str) -> datetime:
        """Combine date and time string into timezone-aware datetime."""
        
        hour, minute = map(int, time_str.split(":"))
        naive = datetime(d.year, d.month, d.day, hour, minute)
        return self.tz.localize(naive)


# Global instance
schedule_service = ScheduleService()
