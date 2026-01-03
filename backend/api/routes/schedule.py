"""
Digital Den — Schedule API Routes
═══════════════════════════════════════════════════════════════════════════

API endpoints for schedule management.
"""

from datetime import date, datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from db.database import get_db
from core.auth import get_current_user_optional
from memory.models import User
from memory.schedule_models import (
    ScheduleItem, ReminderSchedule, ReminderInstance,
    ItemType, ItemStatus, ReminderStatus
)
from core.schedule_service import schedule_service
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/schedule", tags=["Schedule"])


# ═══════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════

class ScheduleItemResponse(BaseModel):
    id: str
    item_type: str
    title: str
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    status: str
    
    class Config:
        from_attributes = True


class ScheduleListResponse(BaseModel):
    items: List[ScheduleItemResponse]
    date: str


class CreateEventRequest(BaseModel):
    title: str
    start_at: datetime
    end_at: Optional[datetime] = None
    duration_minutes: Optional[int] = 60
    description: Optional[str] = None
    category: str = "general"
    remind_before_minutes: int = 15


class CreateTaskRequest(BaseModel):
    title: str
    due_at: datetime
    description: Optional[str] = None
    category: str = "general"
    remind_before_minutes: int = 15


class CreateReminderRequest(BaseModel):
    title: str
    remind_at: datetime
    description: Optional[str] = None
    category: str = "general"


# ═══════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════

async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[User]:
    """Get user by Telegram ID."""
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/today", response_model=ScheduleListResponse)
async def get_today_schedule(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get today's schedule items."""
    return ScheduleListResponse(
        items=[
            ScheduleItemResponse(
                id=str(item.id),
                item_type=item.item_type.value if item.item_type else "reminder",
                title=item.title,
                description=item.description,
                start_at=item.start_at,
                end_at=item.end_at,
                due_at=item.due_at,
                status=item.status.value if item.status else "pending",
            )
            for item in await schedule_service.get_today_schedule(db, current_user.id)
        ],
        date=date.today().isoformat()
    )


@router.get("/range", response_model=ScheduleListResponse)
async def get_schedule_range(
    date_from: date = Query(...),
    date_to: date = Query(...),
    include_completed: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get schedule items for date range."""
    items = await schedule_service.get_schedule(
        db, current_user.id, date_from, date_to, include_completed
    )
    
    return ScheduleListResponse(
        items=[
            ScheduleItemResponse(
                id=str(item.id),
                item_type=item.item_type.value if item.item_type else "reminder",
                title=item.title,
                description=item.description,
                start_at=item.start_at,
                end_at=item.end_at,
                due_at=item.due_at,
                status=item.status.value if item.status else "pending",
            )
            for item in items
        ],
        date=f"{date_from.isoformat()} - {date_to.isoformat()}"
    )


@router.post("/events")
async def create_event(
    request: CreateEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Create a new event."""
    item = await schedule_service.create_event(
        db=db,
        user_id=current_user.id,
        title=request.title,
        start_at=request.start_at,
        end_at=request.end_at,
        duration_minutes=request.duration_minutes,
        description=request.description,
        category=request.category,
        remind_before_minutes=request.remind_before_minutes,
    )
    return {"id": str(item.id), "message": "Event created"}


@router.post("/tasks")
async def create_task(
    request: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Create a new task."""
    item = await schedule_service.create_task(
        db=db,
        user_id=current_user.id,
        title=request.title,
        due_at=request.due_at,
        description=request.description,
        category=request.category,
        remind_before_minutes=request.remind_before_minutes,
    )
    return {"id": str(item.id), "message": "Task created"}


@router.post("/reminders")
async def create_reminder(
    request: CreateReminderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Create a one-time reminder."""
    item = await schedule_service.create_reminder(
        db=db,
        user_id=current_user.id,
        title=request.title,
        remind_at=request.remind_at,
        description=request.description,
        category=request.category,
    )
    return {"id": str(item.id), "message": "Reminder created"}


@router.patch("/items/{item_id}/complete")
async def complete_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Mark item as completed."""
    item = await schedule_service.complete_item(db, item_id, current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item completed"}


@router.patch("/items/{item_id}/skip")
async def skip_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Mark item as skipped."""
    item = await schedule_service.skip_item(db, item_id, current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item skipped"}


# ═══════════════════════════════════════════════════════════════════════════
# Reminder Instance Endpoints
# ═══════════════════════════════════════════════════════════════════════════

reminders_router = APIRouter(prefix="/reminders", tags=["Reminders"])


@reminders_router.post("/{instance_id}/done")
async def mark_reminder_done(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Mark reminder instance as done/confirmed."""
    
    # First try ScheduleItem (primary model for reminders)
    result = await db.execute(
        select(ScheduleItem).where(ScheduleItem.id == instance_id)
    )
    item = result.scalar_one_or_none()
    
    if item:
        item.status = ItemStatus.COMPLETED
        await db.commit()
        logger.info("reminder_confirmed", instance_id=str(instance_id))
        return {"message": "Reminder confirmed"}
    
    # Fallback: try ReminderInstance
    result = await db.execute(
        select(ReminderInstance).where(ReminderInstance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    instance.status = ReminderStatus.CONFIRMED
    instance.confirmed_at = datetime.utcnow()
    await db.commit()
    
    logger.info("reminder_confirmed", instance_id=str(instance_id))
    return {"message": "Reminder confirmed"}



@reminders_router.post("/{instance_id}/snooze")
async def snooze_reminder(
    instance_id: UUID,
    minutes: int = Query(15),
    db: AsyncSession = Depends(get_db),
):
    """Snooze reminder for specified minutes."""
    
    # First try ScheduleItem (primary model for reminders)
    result = await db.execute(
        select(ScheduleItem).where(ScheduleItem.id == instance_id)
    )
    item = result.scalar_one_or_none()
    
    if item:
        item.status = ItemStatus.PENDING  # Will be sent again
        item.start_at = datetime.utcnow() + timedelta(minutes=minutes)
        await db.commit()
        logger.info("reminder_snoozed", instance_id=str(instance_id), minutes=minutes)
        return {"message": f"Reminder snoozed for {minutes} minutes"}
    
    # Fallback: try ReminderInstance
    result = await db.execute(
        select(ReminderInstance).where(ReminderInstance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    instance.status = ReminderStatus.PENDING  # Will be sent again
    instance.snoozed_until = datetime.utcnow() + timedelta(minutes=minutes)
    instance.remind_at = instance.snoozed_until
    await db.commit()
    
    logger.info("reminder_snoozed", instance_id=str(instance_id), minutes=minutes)
    return {"message": f"Reminder snoozed for {minutes} minutes"}


@reminders_router.post("/{instance_id}/skip")
async def skip_reminder(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Mark reminder as skipped/missed."""
    
    # First try ScheduleItem (primary model for reminders)
    result = await db.execute(
        select(ScheduleItem).where(ScheduleItem.id == instance_id)
    )
    item = result.scalar_one_or_none()
    
    if item:
        item.status = ItemStatus.CANCELLED
        await db.commit()
        logger.info("reminder_skipped", instance_id=str(instance_id))
        return {"message": "Reminder skipped"}
    
    # Fallback: try ReminderInstance
    result = await db.execute(
        select(ReminderInstance).where(ReminderInstance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    instance.status = ReminderStatus.MISSED
    await db.commit()
    
    logger.info("reminder_skipped", instance_id=str(instance_id))
    return {"message": "Reminder skipped"}

