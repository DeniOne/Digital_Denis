"""
Digital Denis — Schedule Models
═══════════════════════════════════════════════════════════════════════════

Models for schedule management: events, tasks, reminders.
"""

import uuid
import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, DateTime, Date, Integer, JSON, 
    Enum, ForeignKey, Boolean, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Import Base from memory.models (same as other models)
from memory.models import Base


# ═══════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════

class ItemType(enum.Enum):
    """Тип элемента расписания."""
    EVENT = "event"              # Встреча/событие (имеет длительность)
    TASK = "task"                # Задача (имеет дедлайн)
    REMINDER = "reminder"        # Одноразовое напоминание
    RECURRING = "recurring"      # Повторяющееся напоминание


class ItemStatus(enum.Enum):
    """Статус элемента расписания."""
    PENDING = "pending"          # Ожидает
    IN_PROGRESS = "in_progress"  # В процессе (для задач)
    COMPLETED = "completed"      # Выполнено
    CANCELLED = "cancelled"      # Отменено
    MISSED = "missed"            # Пропущено


class ScheduleType(enum.Enum):
    """Тип повторения для recurring."""
    SINGLE = "single"            # Одноразовое
    DAILY = "daily"              # Каждый день
    WEEKLY = "weekly"            # По дням недели
    INTERVAL = "interval"        # Каждые N дней
    CUSTOM = "custom"            # Сложное расписание


class ReminderStatus(enum.Enum):
    """Статус конкретного напоминания."""
    PENDING = "pending"          # Ожидает отправки
    SENT = "sent"                # Отправлено
    CONFIRMED = "confirmed"      # Пользователь подтвердил выполнение
    MISSED = "missed"            # Пропущено пользователем
    SNOOZED = "snoozed"          # Отложено


# ═══════════════════════════════════════════════════════════════════════════
# Schedule Item — универсальный элемент расписания
# ═══════════════════════════════════════════════════════════════════════════

class ScheduleItem(Base):
    """
    Универсальный элемент расписания.
    Покрывает: события, задачи, напоминания.
    """
    __tablename__ = "schedule_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Тип элемента
    item_type = Column(Enum(ItemType), nullable=False)
    
    # Что
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="general")  # work, personal, health, etc.
    
    # Когда (для event/reminder)
    start_at = Column(DateTime(timezone=True), nullable=True)
    end_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Дедлайн (для task)
    due_at = Column(DateTime(timezone=True), nullable=True)
    
    # Часовой пояс
    timezone = Column(String(50), default="Europe/Moscow")
    
    # Статус
    status = Column(Enum(ItemStatus), default=ItemStatus.PENDING)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Напоминания
    remind_before_minutes = Column(Integer, default=15)
    channels = Column(JSON, default=["telegram", "push"])
    
    # Ссылка на расписание (для recurring)
    schedule_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("reminder_schedules.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # Мета
    source = Column(String(50), default="assistant")  # assistant, manual, telegram, google
    google_event_id = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    user = relationship("User", backref="schedule_items")
    schedule = relationship("ReminderSchedule", back_populates="items")
    
    __table_args__ = (
        Index("idx_schedule_items_user", "user_id"),
        Index("idx_schedule_items_user_status", "user_id", "status"),
        Index("idx_schedule_items_start", "start_at"),
        Index("idx_schedule_items_due", "due_at"),
    )
    
    def __repr__(self):
        return f"<ScheduleItem {self.item_type.value}: {self.title[:30]}>"


# ═══════════════════════════════════════════════════════════════════════════
# Reminder Schedule — шаблон повторяющихся напоминаний
# ═══════════════════════════════════════════════════════════════════════════

class ReminderSchedule(Base):
    """
    Шаблон расписания повторяющихся напоминаний.
    Например: "Таблетки 3 раза в день, 5 дней, перерыв 30".
    """
    __tablename__ = "reminder_schedules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Что напомнить
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="general")  # medication, habit, task, event
    
    # Тип расписания
    schedule_type = Column(Enum(ScheduleType), default=ScheduleType.DAILY)
    
    # Времена в течение дня
    times_of_day = Column(JSON, default=[])  # ["08:00", "14:00", "20:00"]
    
    # Дни недели (для weekly): 1=пн, 7=вс
    days_of_week = Column(JSON, default=[])  # [1, 2, 3, 4, 5]
    
    # Интервал (для interval)
    interval_days = Column(Integer, nullable=True)
    
    # Период действия
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # null = бессрочно
    timezone = Column(String(50), default="Europe/Moscow")
    
    # Напоминание ДО события
    remind_before_minutes = Column(Integer, default=0)
    
    # Каналы доставки
    channels = Column(JSON, default=["telegram", "push"])
    
    # Статус
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    user = relationship("User", backref="reminder_schedules")
    cycle = relationship("ReminderCycle", back_populates="schedule", uselist=False, cascade="all, delete-orphan")
    instances = relationship("ReminderInstance", back_populates="schedule", cascade="all, delete-orphan")
    items = relationship("ScheduleItem", back_populates="schedule")
    
    __table_args__ = (
        Index("idx_reminder_schedules_user", "user_id"),
        Index("idx_reminder_schedules_active", "user_id", "is_active"),
    )
    
    def __repr__(self):
        return f"<ReminderSchedule {self.schedule_type.value}: {self.title[:30]}>"


# ═══════════════════════════════════════════════════════════════════════════
# Reminder Cycle — цикл активности
# ═══════════════════════════════════════════════════════════════════════════

class ReminderCycle(Base):
    """
    Цикл активности для расписания.
    Например: 5 дней приём, 30 дней перерыв, 12 циклов (год).
    """
    __tablename__ = "reminder_cycles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("reminder_schedules.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    
    # Паттерн цикла
    active_days = Column(Integer, nullable=False)   # 5 дней активности
    pause_days = Column(Integer, nullable=False)    # 30 дней перерыв
    
    # Ограничения
    total_cycles = Column(Integer, nullable=True)   # 12 циклов (для года) или null = бессрочно
    
    # Текущее состояние
    current_cycle = Column(Integer, default=1)
    cycle_start_date = Column(Date, nullable=False)
    is_in_pause = Column(Boolean, default=False)
    
    # Связи
    schedule = relationship("ReminderSchedule", back_populates="cycle")
    
    def __repr__(self):
        return f"<ReminderCycle {self.active_days}d/{self.pause_days}d pause>"


# ═══════════════════════════════════════════════════════════════════════════
# Reminder Instance — конкретное напоминание
# ═══════════════════════════════════════════════════════════════════════════

class ReminderInstance(Base):
    """
    Конкретный экземпляр напоминания для отправки.
    Генерируется из ReminderSchedule.
    """
    __tablename__ = "reminder_instances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("reminder_schedules.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Когда напомнить
    remind_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Статус
    status = Column(Enum(ReminderStatus), default=ReminderStatus.PENDING)
    
    # Tracking
    sent_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    snoozed_until = Column(DateTime(timezone=True), nullable=True)
    
    # Повторные попытки
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Какие каналы использованы
    channels_used = Column(JSON, default=[])
    
    # Связи
    schedule = relationship("ReminderSchedule", back_populates="instances")
    logs = relationship("NotificationLog", back_populates="instance", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_reminder_instances_pending", "remind_at", "status"),
        Index("idx_reminder_instances_schedule", "schedule_id"),
        Index("idx_reminder_instances_retry", "next_retry_at", "status"),
    )
    
    def __repr__(self):
        return f"<ReminderInstance {self.remind_at} [{self.status.value}]>"


# ═══════════════════════════════════════════════════════════════════════════
# Notification Log — лог отправок
# ═══════════════════════════════════════════════════════════════════════════

class NotificationLog(Base):
    """Лог отправленных уведомлений."""
    __tablename__ = "notification_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("reminder_instances.id", ondelete="CASCADE"),
        nullable=False
    )
    
    channel = Column(String(50), nullable=False)  # telegram, push, email
    status = Column(String(50), nullable=False)   # sent, failed, delivered
    error_message = Column(Text, nullable=True)
    
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    instance = relationship("ReminderInstance", back_populates="logs")
    
    __table_args__ = (
        Index("idx_notification_logs_instance", "instance_id"),
    )
    
    def __repr__(self):
        return f"<NotificationLog {self.channel} [{self.status}]>"
