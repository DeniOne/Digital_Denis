"""
Digital Denis — Database Models
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

Base = declarative_base()


# ═══════════════════════════════════════════════════════════════════════════
# Memory Items
# ═══════════════════════════════════════════════════════════════════════════

class MemoryItem(Base):
    """
    Core memory item: decision, insight, fact, thought.
    """
    __tablename__ = "memory_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    
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
    
    # Status
    status = Column(String(20), default="active")  # active, archived, aggregated, deleted
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
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

class Topic(Base):
    """
    Topic hierarchy for memory classification.
    """
    __tablename__ = "topics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Hierarchy
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    level = Column(Integer, default=0)
    
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
    user_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Session data
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    source = Column(String(50), default="telegram")  # telegram, web
    metadata_json = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)


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
