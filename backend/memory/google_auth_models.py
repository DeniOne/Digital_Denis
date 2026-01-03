"""
Digital Den — Google Auth Models
═══════════════════════════════════════════════════════════════════════════

Models for storing Google OAuth2 tokens.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from memory.models import Base


class GoogleAuthToken(Base):
    """
    Stores Google OAuth2 tokens for users.
    Required for Google Calendar synchronization.
    """
    __tablename__ = "google_auth_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # OAuth2 Tokens
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)  # Refresh token is only sent once
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Google User Info
    google_email = Column(String(255), nullable=True)
    scopes = Column(JSON, default=[])
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="google_auth")
    
    def __repr__(self):
        return f"<GoogleAuthToken for user {self.user_id}>"


class GoogleCalendarConfig(Base):
    """
    Configuration for Google Calendar sync.
    Shared settings per user.
    """
    __tablename__ = "google_calendar_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    calendar_id = Column(String(255), default="primary")
    is_sync_enabled = Column(DateTime(timezone=True), nullable=True) # Last sync time or null if disabled
    sync_token = Column(Text, nullable=True) # Next sync token for incremental updates
    
    # Behavior
    sync_events = Column(DateTime(timezone=True), nullable=True)
    sync_tasks = Column(DateTime(timezone=True), nullable=True) # Google Tasks (if implemented)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="calendar_config")
