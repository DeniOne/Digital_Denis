"""
Digital Den — Kaizen Engine Models
═══════════════════════════════════════════════════════════════════════════

SQLAlchemy models for Kaizen Engine - personal development tracking.

Based on: docs/kaizen_engine.md, docs/golden_standard_denis.md
"""

import uuid
from datetime import datetime, date
from enum import Enum
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, Float, Boolean, DateTime, ForeignKey,
    Integer, JSON, Date, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from memory.models import Base


# ═══════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════

class KaizenContour(str, Enum):
    """Four contours of Kaizen development."""
    COGNITIVE = "cognitive"       # Ясность мышления
    DECISION = "decision"         # Качество решений
    MANAGEMENT = "management"     # Системность
    STABILITY = "stability"       # Психокогнитивная устойчивость


class UserState(str, Enum):
    """User cognitive states detected by Kaizen Engine."""
    GROWTH = "growth"             # Рост: положительная динамика
    PLATEAU = "plateau"           # Плато: стабильность без роста
    FLUCTUATION = "fluctuation"   # Флуктуации: скачки, противоречия
    OVERLOAD = "overload"         # Перегруз: высокая активность + падение ясности


class TrendDirection(str, Enum):
    """Trend direction for metrics."""
    UP = "up"           # 📈 Рост
    STABLE = "stable"   # ➖ Стабильность
    DOWN = "down"       # 📉 Снижение
    VOLATILE = "volatile"  # ⚠️ Флуктуации


# ═══════════════════════════════════════════════════════════════════════════
# Kaizen Snapshot - Daily state capture
# ═══════════════════════════════════════════════════════════════════════════

class KaizenSnapshot(Base):
    """
    Daily snapshot of user's Kaizen metrics.
    
    The core of relative comparison: 
    user(T) ↔ user(T-1)
    """
    __tablename__ = "kaizen_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Snapshot date
    snapshot_date = Column(Date, nullable=False)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Kaizen Index - aggregated relative dynamics
    # ─────────────────────────────────────────────────────────────────────────
    kaizen_index = Column(Float, default=0.0)  # Relative change from baseline
    kaizen_index_7d = Column(Float, default=0.0)  # Change over 7 days
    kaizen_index_14d = Column(Float, default=0.0)  # Change over 14 days
    kaizen_index_30d = Column(Float, default=0.0)  # Change over 30 days
    
    # Detected user state
    user_state = Column(String(20), default=UserState.PLATEAU.value)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Contour Metrics (0.0 - 1.0 scale, relative to personal baseline)
    # ─────────────────────────────────────────────────────────────────────────
    
    # Cognitive Contour (Когнитивный)
    cognitive_score = Column(Float, default=0.5)
    cognitive_trend = Column(String(20), default=TrendDirection.STABLE.value)
    cognitive_change_pct = Column(Float, default=0.0)  # % change from previous
    
    # Decision Contour (Решенческий)
    decision_score = Column(Float, default=0.5)
    decision_trend = Column(String(20), default=TrendDirection.STABLE.value)
    decision_change_pct = Column(Float, default=0.0)
    
    # Management Contour (Системность)
    management_score = Column(Float, default=0.5)
    management_trend = Column(String(20), default=TrendDirection.STABLE.value)
    management_change_pct = Column(Float, default=0.0)
    
    # Stability Contour (Устойчивость)
    stability_score = Column(Float, default=0.5)
    stability_trend = Column(String(20), default=TrendDirection.STABLE.value)
    stability_change_pct = Column(Float, default=0.0)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Raw Metrics (inputs for contour calculation)
    # ─────────────────────────────────────────────────────────────────────────
    
    # Linguistic patterns
    avg_message_length = Column(Float, default=0.0)
    formulation_precision = Column(Float, default=0.0)  # Точность запросов
    abstraction_level = Column(Float, default=0.0)  # Уровень абстракции
    
    # Behavioral patterns
    topic_switches = Column(Integer, default=0)  # Резкие смены тем
    decision_completion_rate = Column(Float, default=0.0)  # Доведение до результата
    revisit_rate = Column(Float, default=0.0)  # Возврат к тем же темам
    
    # Activity metrics
    messages_count = Column(Integer, default=0)
    decisions_count = Column(Integer, default=0)
    insights_count = Column(Integer, default=0)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Kaizen Mirror - reflective observations (1-2 sentences)
    # ─────────────────────────────────────────────────────────────────────────
    mirror_observation = Column(Text, nullable=True)
    
    # Additional metadata
    meta_data = Column("metadata", JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_kaizen_snapshot_user_date", "user_id", "snapshot_date"),
        Index("idx_kaizen_snapshot_date", "snapshot_date"),
        Index("idx_kaizen_snapshot_state", "user_state"),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Contour Metrics History - detailed per-contour tracking
# ═══════════════════════════════════════════════════════════════════════════

class KaizenContourMetrics(Base):
    """
    Detailed metrics for each Kaizen contour.
    Allows granular analysis of each development dimension.
    """
    __tablename__ = "kaizen_contour_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("kaizen_snapshots.id", ondelete="CASCADE"), nullable=False)
    
    # Which contour
    contour = Column(String(20), nullable=False)  # cognitive, decision, management, stability
    
    # Score and trend
    score = Column(Float, default=0.5)
    trend = Column(String(20), default=TrendDirection.STABLE.value)
    change_pct = Column(Float, default=0.0)
    
    # Sub-metrics (contour-specific)
    sub_metrics = Column(JSONB, default={})
    
    # Factors that influenced this score
    influence_factors = Column(JSONB, default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_kaizen_contour_snapshot", "snapshot_id"),
        Index("idx_kaizen_contour_type", "contour"),
    )


# ═══════════════════════════════════════════════════════════════════════════
# State Transitions - tracking how user state changes
# ═══════════════════════════════════════════════════════════════════════════

class KaizenStateTransition(Base):
    """
    Records when user's cognitive state changes.
    Helps identify patterns in state evolution.
    """
    __tablename__ = "kaizen_state_transitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # State change
    from_state = Column(String(20), nullable=False)
    to_state = Column(String(20), nullable=False)
    
    # When it happened
    transition_date = Column(Date, nullable=False)
    
    # What caused it (observation, not judgment)
    probable_factors = Column(JSONB, default=[])
    
    # Duration in previous state (days)
    previous_state_duration = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_kaizen_transition_user", "user_id"),
        Index("idx_kaizen_transition_date", "transition_date"),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Kaizen Observations - AI-generated insights in neutral language
# ═══════════════════════════════════════════════════════════════════════════

class KaizenObservation(Base):
    """
    Neutral, non-judgmental observations about thinking patterns.
    
    Language rules:
    ✅ "наблюдается", "зафиксировано", "изменилось"
    ❌ "нужно", "должен", "проблема"
    """
    __tablename__ = "kaizen_observations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # When observed
    observation_date = Column(Date, nullable=False)
    
    # Related contour (optional)
    contour = Column(String(20), nullable=True)
    
    # The observation (neutral language)
    observation_text = Column(Text, nullable=False)
    
    # Type: pattern, change, notable, reflection
    observation_type = Column(String(30), default="pattern")
    
    # Confidence in this observation
    confidence = Column(Float, default=0.7)
    
    # Related snapshot
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("kaizen_snapshots.id", ondelete="SET NULL"), nullable=True)
    
    # Is this suitable for "Kaizen Mirror" display?
    is_mirror_worthy = Column(Boolean, default=False)
    
    # Has user seen this?
    is_viewed = Column(Boolean, default=False)
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_kaizen_obs_user", "user_id"),
        Index("idx_kaizen_obs_date", "observation_date"),
        Index("idx_kaizen_obs_mirror", "is_mirror_worthy"),
    )
