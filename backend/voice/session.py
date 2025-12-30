from datetime import datetime
from typing import Optional
import uuid

class VoiceSession:
    """
    Represents an active voice session for a user.
    """
    def __init__(self, user_id: str):
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        self.started_at = datetime.utcnow()
        self.last_activity = self.started_at
        self.is_active = True
        self.messages_count = 0
        self.total_audio_bytes = 0

    def touch(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def add_metric_audio(self, size: int):
        """Track metrics."""
        self.total_audio_bytes += size
        self.messages_count += 1

    def close(self):
        """Mark session as closed."""
        self.is_active = False

    @property
    def duration_seconds(self) -> float:
        """Get session duration."""
        return (datetime.utcnow() - self.started_at).total_seconds()
