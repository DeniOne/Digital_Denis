"""
Digital Den — Base Agent
═══════════════════════════════════════════════════════════════════════════

Abstract base class for all agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import UUID


@dataclass
class AgentContext:
    """Context passed to agent for processing."""
    
    session_id: UUID
    user_message: str
    
    # Chat history (last N messages)
    history: List[Dict[str, str]] = field(default_factory=list)
    
    # Relevant memories from long-term storage
    memories: List[Dict[str, Any]] = field(default_factory=list)
    
    # Profile system prompt
    system_prompt: str = ""
    
    # Request classification
    request_type: Optional[str] = None  # strategic, analytical, operational, reflexive, meta
    
    # Model role for hybrid AI architecture
    model_role: Optional[str] = None  # router, fast, thinking, creative_text, etc.
    
    # User settings (AI behavior, rules, etc.)
    user_settings: Optional[Any] = None  # UserSettingsContext
    
    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Database session and User ID
    db: Optional[Any] = None
    user_id: Optional[UUID] = None


@dataclass
class AgentResponse:
    """Response from agent."""
    
    content: str
    agent: str  # agent name
    
    # Should this be saved to memory?
    save_to_memory: bool = False
    memory_type: Optional[str] = None  # decision, insight, fact, thought
    memory_data: Optional[Dict[str, Any]] = None
    
    # Metadata
    confidence: float = 0.5
    tokens_used: int = 0
    
    # Follow-up actions
    follow_up: Optional[str] = None  # agent to call next, if any


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Agents are specialized components that process user requests.
    Each agent has a specific role and set of capabilities.
    """
    
    name: str = "base"
    description: str = "Base agent"
    
    # Does this agent participate in dialogue?
    participates_in_dialogue: bool = True
    
    # Does this agent write to memory?
    writes_to_memory: bool = False
    
    # Is this agent synchronous?
    is_synchronous: bool = True
    
    @abstractmethod
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process user request and return response.
        
        This is the main entry point for agent logic.
        """
        pass
    
    async def pre_process(self, context: AgentContext) -> AgentContext:
        """
        Pre-processing hook. Override to modify context before processing.
        """
        return context
    
    async def post_process(
        self, 
        context: AgentContext, 
        response: AgentResponse
    ) -> AgentResponse:
        """
        Post-processing hook. Override to modify response after processing.
        """
        return response
    
    async def run(self, context: AgentContext) -> AgentResponse:
        """
        Full agent execution pipeline.
        """
        # Pre-process
        context = await self.pre_process(context)
        
        # Main processing
        response = await self.process(context)
        
        # Post-process
        response = await self.post_process(context, response)
        
        return response
