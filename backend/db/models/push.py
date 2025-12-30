from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from memory.models import Base  # Import Base from where User is defined

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    endpoint = Column(String, unique=True, nullable=False)
    keys = Column(JSON, nullable=False)  # {"p256dh": "...", "auth": "..."}
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="push_subscriptions")
