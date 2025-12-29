"""
Digital Denis — Context Manager
═══════════════════════════════════════════════════════════════════════════

Assembles context for agents: session, memory, profile.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Any
from uuid import UUID, uuid4

from memory.short_term import short_term_memory
from memory.long_term import long_term_memory
from orchestrator.profile import get_profile, DigitalProfile


@dataclass
class Message:
    """Chat message structure."""
    role: str  # user, assistant
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    agent: Optional[str] = None


@dataclass
class MemoryItem:
    """Memory item from long-term storage."""
    id: UUID
    content: str
    item_type: str  # decision, insight, fact
    summary: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Topic:
    """Topic classification."""
    id: UUID
    name: str
    confidence: float = 0.5


@dataclass
class AssembledContext:
    """
    Full context assembled for agent processing.
    
    Contains all information an agent needs to process a request:
    - User message and classification
    - Digital Profile constraints
    - Session history
    - Relevant memories
    - Active topics
    """
    # Request
    message: str
    message_type: str  # strategic, analytical, operational, reflexive, meta
    request_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Session
    session_id: UUID = field(default_factory=uuid4)
    conversation_history: List[Message] = field(default_factory=list)
    
    # Profile
    profile: Optional[DigitalProfile] = None
    system_prompt: str = ""
    
    # Memory
    relevant_memories: List[MemoryItem] = field(default_factory=list)
    active_topics: List[Topic] = field(default_factory=list)
    
    # Metadata
    metadata: dict = field(default_factory=dict)


class ContextManager:
    """
    Manages context assembly for agent processing.
    
    Responsibilities:
    1. Session management (via Redis)
    2. Memory retrieval (relevant memories)
    3. Context assembly (profile + session + memory)
    """
    
    def __init__(self):
        self.profile = get_profile()
    
    async def get_session(self, session_id: str) -> dict:
        """
        Get or create session from Redis.
        
        Returns session context with:
        - started_at
        - last_activity
        - active_topics
        - current_mode
        """
        session = await short_term_memory.get_session(session_id)
        
        if not session:
            session = {
                "started_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "active_topics": [],
                "current_mode": "default",
            }
            await short_term_memory.save_session(session_id, session)
        
        return session
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: int = 10
    ) -> List[Message]:
        """Get recent conversation history from Redis."""
        history = await short_term_memory.get_chat_history(session_id, limit)
        
        return [
            Message(
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                timestamp=datetime.fromisoformat(msg["timestamp"]) 
                    if msg.get("timestamp") else datetime.utcnow(),
                agent=msg.get("agent"),
            )
            for msg in history
        ]
    
    async def get_relevant_memories(
        self,
        query: str,
        db: Any,
        limit: int = 5,
        item_types: Optional[List[str]] = None,
    ) -> List[MemoryItem]:
        """
        Get memories relevant to the current query.
        
        For now: simple text-based search.
        Future: semantic search with embeddings.
        """
        try:
            items = await long_term_memory.search(
                db=db,
                query=query,
                limit=limit,
            )
            
            return [
                MemoryItem(
                    id=item.id,
                    content=item.content,
                    item_type=item.item_type,
                    summary=item.summary,
                    created_at=item.created_at,
                )
                for item in items
            ]
        except Exception:
            return []
    
    async def assemble(
        self,
        message: str,
        message_type: str,
        session_id: Optional[UUID] = None,
        db: Any = None,
        include_memories: bool = True,
    ) -> AssembledContext:
        """
        Assemble full context for agent processing.
        
        Steps:
        1. Get/create session
        2. Load conversation history
        3. Retrieve relevant memories
        4. Build system prompt from profile
        5. Package everything into AssembledContext
        """
        session_id = session_id or uuid4()
        session_id_str = str(session_id)
        
        # Get session
        session = await self.get_session(session_id_str)
        
        # Get conversation history
        history = await self.get_conversation_history(session_id_str)
        
        # Get relevant memories
        memories = []
        if include_memories and db:
            memories = await self.get_relevant_memories(
                query=message,
                db=db,
                limit=5,
            )
        
        # Build system prompt
        system_prompt = self.profile.get_system_prompt() if self.profile else ""
        
        # Assemble context
        context = AssembledContext(
            message=message,
            message_type=message_type,
            session_id=session_id,
            conversation_history=history,
            profile=self.profile,
            system_prompt=system_prompt,
            relevant_memories=memories,
            active_topics=[
                Topic(id=uuid4(), name=t) 
                for t in session.get("active_topics", [])
            ],
            metadata={
                "session": session,
            },
        )
        
        return context
    
    async def update_session_topics(
        self, 
        session_id: str, 
        topics: List[str]
    ) -> None:
        """Update active topics for session."""
        session = await self.get_session(session_id)
        session["active_topics"] = topics
        session["last_activity"] = datetime.utcnow().isoformat()
        await short_term_memory.save_session(session_id, session)


# Global instance
context_manager = ContextManager()
