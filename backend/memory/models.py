"""
Digital Den — Database Models
═══════════════════════════════════════════════════════════════════════════

SQLAlchemy models for Memory Layer.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, Float, Boolean, DateTime, ForeignKey,
    Integer, JSON, ARRAY, Index, create_engine
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

EMBEDDING_DIMENSION = 1536  # OpenAI ada-002 / OpenRouter embeddings

Base = declarative_base()


# ═══════════════════════════════════════════════════════════════════════════
# Shared Tables
# ═══════════════════════════════════════════════════════════════════════════

class PushSubscription(Base):
    """
    Push notification subscription for Web Push.
    """
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    endpoint = Column(String, unique=True, nullable=False)
    keys = Column(JSON, nullable=False)  # {"p256dh": "...", "auth": "..."}
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="push_subscriptions")


# ═══════════════════════════════════════════════════════════════════════════
# Users
# ═══════════════════════════════════════════════════════════════════════════

class User(Base):
    """
    System user (owner or viewer).
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(Integer, unique=True, nullable=True)
    username = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    
    # Role: owner, viewer, api
    role = Column(String(20), default="owner")
    
    # Flags
    is_active = Column(Boolean, default=True)
    notification_settings = Column(JSON, default={"quiet_hours_start": "23:00", "quiet_hours_end": "08:00", "enabled_types": ["all"]})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    memories = relationship("MemoryItem", back_populates="user")
    sessions = relationship("Session", back_populates="user")
    push_subscriptions = relationship("PushSubscription", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username or self.telegram_id}>"


# ═══════════════════════════════════════════════════════════════════════════
# Memory Items
# ═══════════════════════════════════════════════════════════════════════════

class MemoryItem(Base):
    """
    Core memory item: decision, insight, fact, thought.
    """
    __tablename__ = "memory_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Type classification
    item_type = Column(String(50), nullable=False)  # decision, insight, fact, thought
    
    # Content
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)  # LLM-generated summary
    
    # Structured data (for decisions)
    structured_data = Column(JSON, nullable=True)
    
    # Metadata
    source_agent = Column(String(50), nullable=True)  # which agent created
    source_session = Column(UUID(as_uuid=True), nullable=True)
    confidence = Column(Float, default=0.5)
    
    # RAG 2.0 fields
    related_to = Column(ARRAY(UUID(as_uuid=True)), nullable=True)  # связи с другими воспоминаниями
    usage_count = Column(Integer, default=0)  # сколько раз использовалось
    positive_outcomes = Column(Integer, default=0)  # позитивные исходы
    negative_outcomes = Column(Integer, default=0)  # негативные исходы
    confidence_level = Column(String(16), default="medium")  # high, medium, low, unknown
    
    # Status
    status = Column(String(20), default="active")  # active, archived, aggregated, deleted
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="memories")
    topics = relationship("MemoryTopic", back_populates="memory", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_memory_items_user", "user_id"),
        Index("idx_memory_items_type", "item_type"),
        Index("idx_memory_items_status", "status"),
        Index("idx_memory_items_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<MemoryItem {self.item_type}: {self.content[:50]}...>"


# ═══════════════════════════════════════════════════════════════════════════
# Topics
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# Memory Events (Metapamory)
# ═══════════════════════════════════════════════════════════════════════════

class MemoryEvent(Base):
    """
    Tracking memory usage and effectiveness.
    """
    __tablename__ = "memory_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memory_items.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    event_type = Column(String(32), nullable=False)  # recalled, used, rejected, archived
    outcome = Column(String(16), nullable=True)      # positive, neutral, negative, unknown
    
    context = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    memory = relationship("MemoryItem", backref="events")
    user = relationship("User", backref="memory_events")
    
    # Indexes
    __table_args__ = (
        Index("idx_memory_events_memory", "memory_id"),
        Index("idx_memory_events_user", "user_id"),
        Index("idx_memory_events_type", "event_type"),
        Index("idx_memory_events_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<MemoryEvent {self.event_type} for {self.memory_id}>"


class KaizenMetric(Base):
    """
    Kaizen metrics for user's thinking quality trends.
    """
    __tablename__ = "kaizen_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    dimension = Column(String(32), nullable=False)  # decision_quality, consistency, clarity_of_thought, execution, emotional_stability
    score = Column(Float, nullable=False)            # 0.0 - 100.0
    
    context = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="kaizen_metrics")
    
    # Indexes
    __table_args__ = (
        Index("idx_kaizen_metrics_user", "user_id"),
        Index("idx_kaizen_metrics_dimension", "dimension"),
        Index("idx_kaizen_metrics_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<KaizenMetric {self.dimension}: {self.score}>"


class ConversationState(Base):
    """
    Explicit dialog state tracking for low-bandwidth channels (Telegram).
    """
    __tablename__ = "conversation_states"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(String(255), nullable=False)  # chat_id from Telegram
    
    # Core state
    topic = Column(Text, nullable=True)
    goal = Column(Text, nullable=True)
    current_step = Column(Text, nullable=True)
    intent = Column(String(50), nullable=True)
    
    # Entities and objects
    active_entities = Column(ARRAY(Text), default=[])
    active_objects = Column(ARRAY(Text), default=[])
    
    # Assumptions and constraints
    assumptions = Column(ARRAY(Text), default=[])
    constraints = Column(ARRAY(Text), default=[])
    
    # Decisions and questions
    decisions_made = Column(JSON, default=[])
    open_questions = Column(ARRAY(Text), default=[])
    unresolved_points = Column(ARRAY(Text), default=[])
    
    # Confidence
    confidence_level = Column(String(16), default="unknown")
    
    # TTL
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ttl_hours = Column(Integer, default=48)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="conversation_states")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_conversation_states_user", "user_id"),
        Index("idx_conversation_states_conv_id", "conversation_id"),
        Index("idx_conversation_states_updated", "last_updated"),
    )
    
    def to_dict(self):
        """Convert to dict for JSON serialization"""
        return {
            "conversation_id": self.conversation_id,
            "topic": self.topic,
            "goal": self.goal,
            "current_step": self.current_step,
            "intent": self.intent,
            "active_entities": self.active_entities or [],
            "active_objects": self.active_objects or [],
            "assumptions": self.assumptions or [],
            "constraints": self.constraints or [],
            "decisions_made": self.decisions_made or [],
            "open_questions": self.open_questions or [],
            "unresolved_points": self.unresolved_points or [],
            "confidence_level": self.confidence_level,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "ttl_hours": self.ttl_hours,
        }
    
    def __repr__(self):
        return f"<ConversationState {self.conversation_id}: {self.topic}>"


# ═══════════════════════════════════════════════════════════════════════════
# Topics
# ═══════════════════════════════════════════════════════════════════════════

class Topic(Base):
    """
    Topic hierarchy for memory classification.
    """
    __tablename__ = "topics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Hierarchy
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)  # Slug is unique within scope
    parent_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    level = Column(Integer, default=0)
    
    # Ownership & Source
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    is_auto_generated = Column(Boolean, default=False)
    cluster_id = Column(String(100), nullable=True)  # To group topics from same run
    
    # Description
    description = Column(Text, nullable=True)
    keywords = Column(ARRAY(String), nullable=True)
    
    # Configuration
    is_system = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Stats (denormalized)
    item_count = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="topics")
    
    # Indexes & UNIQUE
    __table_args__ = (
        Index("idx_topics_parent", "parent_id"),
        Index("idx_topics_user", "user_id"),
        Index("idx_topics_slug", "slug"),
        # We allow same slug for different users, or if it's a system topic
        # But for simplicity, we'll keep it globally unique or unique per user
    )
    
    # Relationships
    parent = relationship("Topic", remote_side=[id], backref="children")
    memories = relationship("MemoryTopic", back_populates="topic")
    
    # Indexes
    __table_args__ = (
        Index("idx_topics_parent", "parent_id"),
        Index("idx_topics_slug", "slug"),
    )
    
    def __repr__(self):
        return f"<Topic {self.slug}>"


# ═══════════════════════════════════════════════════════════════════════════
# Memory-Topic Link
# ═══════════════════════════════════════════════════════════════════════════

class MemoryTopic(Base):
    """
    Many-to-many link between memory items and topics.
    """
    __tablename__ = "memory_topics"
    
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memory_items.id", ondelete="CASCADE"), primary_key=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    
    # Classification confidence
    confidence = Column(Float, default=0.5)
    
    # Source
    assigned_by = Column(String(50), default="llm")  # llm, user, rule
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    memory = relationship("MemoryItem", back_populates="topics")
    topic = relationship("Topic", back_populates="memories")
    
    # Indexes
    __table_args__ = (
        Index("idx_memory_topics_topic", "topic_id"),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Sessions
# ═══════════════════════════════════════════════════════════════════════════

class Session(Base):
    """
    User session tracking.
    """
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Session data
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    source = Column(String(50), default="telegram")  # telegram, web
    metadata_json = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="sessions")


# ═══════════════════════════════════════════════════════════════════════════
# Messages (for history)
# ═══════════════════════════════════════════════════════════════════════════

class Message(Base):
    """
    Message history within sessions.
    """
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    
    # Agent info
    agent = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index("idx_messages_session", "session_id"),
        Index("idx_messages_created", "created_at"),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Audit
# ═══════════════════════════════════════════════════════════════════════════

class AuditLog(Base):
    """
    Audit trail for critical user actions.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    action = Column(String(50), nullable=False)  # e.g., "login", "memory_create"
    target_type = Column(String(50))  # e.g., "memory_item"
    target_id = Column(String(50))  # UUID as string
    
    changes = Column(JSON, default={})  # {"field": {"old": "val", "new": "val"}}
    meta_data = Column("metadata", JSON, default={})  # Extra context: ip, user_agent
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="audit_logs")


# ═══════════════════════════════════════════════════════════════════════════
# Embeddings
# ═══════════════════════════════════════════════════════════════════════════

class MemoryEmbedding(Base):
    """
    Stores vector embeddings for memory items.
    Separate table to keep main table clean.
    """
    __tablename__ = "memory_embeddings"
    
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memory_items.id", ondelete="CASCADE"), primary_key=True)
    embedding = Column(Vector(EMBEDDING_DIMENSION), nullable=False)
    model = Column(String(100), default="text-embedding-ada-002")
    
    # Relationships
    memory = relationship("MemoryItem", backref="vector_embedding")

    def __repr__(self):
        return f"<MemoryEmbedding for {self.memory_id}>"


# ═══════════════════════════════════════════════════════════════════════════
# User Settings (AI Control)
# ═══════════════════════════════════════════════════════════════════════════

class UserSettings(Base):
    """
    AI Control settings for user.
    Defines how AI behaves, thinks, and interacts.
    """
    __tablename__ = "user_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Behavior Settings
    # ═══════════════════════════════════════════════════════════════════════
    
    # AI Role: partner_strategic, analyst_logical, coach_socratic, recorder_passive, explorer_hypothesis
    ai_role = Column(String(50), default="partner_strategic")
    
    # Thinking Depth: shallow, structured, systemic, philosophical
    thinking_depth = Column(String(30), default="structured")
    
    # Response Style: short, detailed
    response_style = Column(String(20), default="detailed")
    
    # Confrontation Level: none, soft, argumented, hard
    confrontation_level = Column(String(20), default="argumented")
    
    # ═══════════════════════════════════════════════════════════════════════
    # Autonomy Settings
    # ═══════════════════════════════════════════════════════════════════════
    
    # Initiative: request_only, suggest, warn, proactive
    initiative_level = Column(String(30), default="suggest")
    
    # Intervention Frequency: realtime, post_session, daily_review, anomaly_detected
    intervention_frequency = Column(String(30), default="realtime")
    
    # Allowed Actions: JSON array ['create_decisions', 'link_memories', 'refactor_thoughts', 'challenge_beliefs']
    allowed_actions = Column(JSON, default=["create_decisions", "link_memories"])
    
    # ═══════════════════════════════════════════════════════════════════════
    # Memory Settings
    # ═══════════════════════════════════════════════════════════════════════
    
    # Save Policy: save_all, save_confirmed, save_marked
    save_policy = Column(String(30), default="save_confirmed")
    
    # Auto Archive Days (0 = disabled)
    auto_archive_days = Column(Integer, default=365)
    
    # Memory Trust Level: none, cautious, trusted
    memory_trust_level = Column(String(20), default="cautious")
    
    # Saved types: JSON array ['facts', 'decisions', 'hypotheses', 'emotional_states', 'behavioral_patterns']
    saved_types = Column(JSON, default=["facts", "decisions", "hypotheses"])
    
    # ═══════════════════════════════════════════════════════════════════════
    # Analytics Settings
    # ═══════════════════════════════════════════════════════════════════════
    
    # Analytics Types: JSON array ['logical_contradictions', 'recurring_topics', 'trend_deviation', 'cognitive_biases', 'focus_loss']
    analytics_types = Column(JSON, default=["logical_contradictions", "recurring_topics"])
    
    # Aggressiveness: inform, recommend, warn, demand_attention
    analytics_aggressiveness = Column(String(30), default="recommend")
    
    # ═══════════════════════════════════════════════════════════════════════
    # Explain Mode Settings
    # ═══════════════════════════════════════════════════════════════════════
    
    # Explain Mode: off, brief, detailed
    # When enabled, AI explains its reasoning in responses
    explain_mode = Column(String(20), default="off")
    
    # ═══════════════════════════════════════════════════════════════════════
    # Kaizen Engine Settings
    # ═══════════════════════════════════════════════════════════════════════
    
    # Enable Adaptive AI Behavior based on user state
    kaizen_adaptive_ai_enabled = Column(Boolean, default=True)
    
    # Show Kaizen Mirror (reflective observations)
    kaizen_show_mirror = Column(Boolean, default=True)
    
    # Comparison period: week, month, quarter, half_year, year, all_time
    kaizen_comparison_period = Column(String(20), default="month")
    
    # ═══════════════════════════════════════════════════════════════════════
    # Timestamps
    # ═══════════════════════════════════════════════════════════════════════
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="settings")
    
    def __repr__(self):
        return f"<UserSettings for user {self.user_id}>"

