"""
Digital Den — Redis Client
═══════════════════════════════════════════════════════════════════════════

Short-term memory operations with Redis.
"""

import json
from datetime import timedelta
from typing import Optional, List, Dict, Any

import redis.asyncio as redis

from core.config import settings


class ShortTermMemory:
    """
    Short-term memory using Redis.
    
    Stores:
    - Session context (TTL: 1 hour)
    - Chat history (TTL: 24 hours)
    - Working buffer (TTL: 5 minutes)
    """
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        
        # TTL settings
        self.session_ttl = timedelta(hours=1)
        self.chat_ttl = timedelta(hours=24)
        self.buffer_ttl = timedelta(minutes=5)
    
    async def connect(self):
        """Connect to Redis."""
        self.redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Session Context
    # ─────────────────────────────────────────────────────────────────────────
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session context."""
        key = f"session:{session_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def set_session(self, session_id: str, data: Dict[str, Any]):
        """Set session context."""
        key = f"session:{session_id}"
        await self.redis.setex(
            key,
            self.session_ttl,
            json.dumps(data, ensure_ascii=False),
        )
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Update session context."""
        current = await self.get_session(session_id) or {}
        current.update(updates)
        await self.set_session(session_id, current)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Chat History
    # ─────────────────────────────────────────────────────────────────────────
    
    async def get_chat_history(
        self, 
        session_id: str, 
        limit: int = 20
    ) -> List[Dict[str, str]]:
        """Get chat history for session."""
        key = f"chat:{session_id}"
        data = await self.redis.lrange(key, -limit, -1)
        return [json.loads(msg) for msg in data]
    
    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        agent: Optional[str] = None
    ):
        """Add message to chat history."""
        key = f"chat:{session_id}"
        message = {
            "role": role,
            "content": content,
            "agent": agent,
        }
        await self.redis.rpush(key, json.dumps(message, ensure_ascii=False))
        await self.redis.expire(key, int(self.chat_ttl.total_seconds()))
        
        # Keep only last 200 messages
        await self.redis.ltrim(key, -200, -1)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Working Buffer
    # ─────────────────────────────────────────────────────────────────────────
    
    async def set_buffer(self, request_id: str, data: Dict[str, Any]):
        """Set working buffer for request processing."""
        key = f"buffer:{request_id}"
        await self.redis.setex(
            key,
            self.buffer_ttl,
            json.dumps(data, ensure_ascii=False),
        )
    
    async def get_buffer(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get working buffer."""
        key = f"buffer:{request_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def delete_buffer(self, request_id: str):
        """Delete working buffer."""
        key = f"buffer:{request_id}"
        await self.redis.delete(key)


# Global instance
short_term_memory = ShortTermMemory()
