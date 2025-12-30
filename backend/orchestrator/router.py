"""
Digital Denis — Request Router
═══════════════════════════════════════════════════════════════════════════

Routes incoming requests to appropriate agents.
"""

from typing import Optional
from uuid import UUID, uuid4

from agents.base import AgentContext, AgentResponse
from agents.core_agent import core_agent
from agents.memory_agent import memory_agent
from orchestrator.profile import get_profile
from memory.short_term import short_term_memory
from llm.groq import groq
from core.logging import get_logger

logger = get_logger(__name__)


class RequestRouter:
    """
    Routes requests to appropriate agents based on classification.
    
    Request types:
    - strategic: long-term planning, vision
    - analytical: data analysis, numbers
    - operational: tasks, actions
    - reflexive: meta-thinking, self-analysis
    - meta: about the system itself
    """
    
    def __init__(self):
        self.profile = get_profile()
        
        # Agent mapping
        self.agents = {
            "strategic": core_agent,
            "analytical": core_agent,  # Will be Analyst Agent in v0.2
            "operational": core_agent,  # Will be Operator Agent in v0.2
            "reflexive": core_agent,
            "meta": core_agent,
        }
        
        # Default agent
        self.default_agent = core_agent
    
    async def route(
        self,
        user_message: str,
        session_id: Optional[UUID] = None,
        db=None,
        user_id: Optional[UUID] = None,
    ) -> AgentResponse:
        """
        Route request to appropriate agent and return response.
        """
        # Generate session ID if not provided
        session_id = session_id or uuid4()
        
        # Classify request
        request_type = await self._classify_request(user_message)
        
        # Get chat history from Redis
        history = await short_term_memory.get_chat_history(str(session_id))
        
        # Get relevant memories
        memories = []
        if db:
            memories = await memory_agent.get_context_memories(
                db=db,
                user_message=user_message,
                user_id=user_id,
            )
        
        # Build context
        context = AgentContext(
            session_id=session_id,
            user_message=user_message,
            history=history,
            memories=memories,
            system_prompt=self.profile.get_system_prompt(),
            request_type=request_type,
        )
        
        # Select agent
        agent = self.agents.get(request_type, self.default_agent)
        
        logger.info(
            "request_routed",
            request_type=request_type,
            agent=agent.name,
            session_id=str(session_id),
            message_length=len(user_message)
        )
        
        # Process request
        response = await agent.run(context)
        
        # Save to chat history
        await short_term_memory.add_message(
            session_id=str(session_id),
            role="user",
            content=user_message,
        )
        await short_term_memory.add_message(
            session_id=str(session_id),
            role="assistant",
            content=response.content,
            agent=response.agent,
        )
        
        # Save to long-term memory if needed
        if response.save_to_memory and db:
            await memory_agent.save_from_response(
                db=db,
                response=response,
                session_id=session_id,
                user_message=user_message,
                user_id=user_id,
            )
        
        return response
    
    async def _classify_request(self, message: str) -> str:
        """Classify request type using cheap LLM."""
        
        prompt = f"""Classify this request into one category:
- strategic: long-term planning, vision, strategy
- analytical: data analysis, numbers, metrics
- operational: tasks, actions, to-do
- reflexive: thinking about thinking, self-analysis
- meta: about this AI system

Request: {message[:200]}

Return only the category name:"""
        
        try:
            result = await groq.complete_simple(prompt)
            category = result.strip().lower()
            if category in self.agents:
                return category
        except Exception:
            pass
        
        return "operational"  # Default


# Global instance
router = RequestRouter()
