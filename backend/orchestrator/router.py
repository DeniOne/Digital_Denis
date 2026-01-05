"""
Digital Den — Request Router
═══════════════════════════════════════════════════════════════════════════

Routes incoming requests to appropriate agents.
"""

from typing import Optional
from uuid import UUID, uuid4

from agents.base import AgentContext, AgentResponse
from agents.core_agent import core_agent
from agents.memory_agent import memory_agent
from agents.schedule_agent import schedule_agent
from orchestrator.profile import get_profile
from orchestrator.user_settings import get_user_settings
from orchestrator.intent_analyzer import intent_analyzer, IntentAnalysis
from orchestrator.adaptive_behavior import adaptive_behavior
from analytics.kaizen_models import UserState
from memory.short_term import short_term_memory
from core.logging import get_logger
from llm.model_router import model_router, TaskCategory

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
    - schedule: reminders, events, tasks
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
            "schedule": schedule_agent,
            "creative": core_agent,
            "social": core_agent,
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
        
        # ═══════════════════════════════════════════════════════════════════
        # Hybrid AI: Classify task for optimal model selection
        # ═══════════════════════════════════════════════════════════════════
        task_category, model_role, model_confidence = await model_router.classify(user_message)
        
        logger.info(
            "model_selected",
            task_category=task_category.value,
            model_role=model_role.value,
            model_confidence=model_confidence,
        )
        
        # Analyze intent (extended analysis)
        intent = await intent_analyzer.analyze(user_message)
        
        # Get chat history from Redis
        history = await short_term_memory.get_chat_history(str(session_id))
        
        logger.info(
            "request_received",
            session_id=str(session_id),
            history_len=len(history),
            user_id=str(user_id) if user_id else None
        )
        
        # Get relevant memories
        memories = []
        if db:
            memories = await memory_agent.get_context_memories(
                db=db,
                user_message=user_message,
                user_id=user_id,
            )
        
        # Load user settings
        user_settings = None
        if db and user_id:
            user_settings = await get_user_settings(db, user_id)
        
        # ═══════════════════════════════════════════════════════════════════
        # Kaizen Engine: Load user state for adaptive behavior
        # ═══════════════════════════════════════════════════════════════════
        user_kaizen_state = UserState.PLATEAU  # Default
        kaizen_contours = None
        
        if db and user_id:
            try:
                from analytics.kaizen_service import KaizenEngine
                kaizen_engine = KaizenEngine(db)
                kaizen_data = await kaizen_engine.get_user_state_for_ai(user_id)
                user_kaizen_state = UserState(kaizen_data.get("state", "plateau"))
                kaizen_contours = kaizen_data.get("contours")
                
                logger.info(
                    "kaizen_state_loaded",
                    user_id=str(user_id),
                    state=user_kaizen_state.value,
                )
            except Exception as e:
                logger.warning(
                    "kaizen_state_load_failed",
                    error=str(e),
                )
        
        # Build system prompt with user settings and emotional awareness
        base_prompt = self.profile.get_system_prompt()
        if user_settings:
            full_prompt = base_prompt + user_settings.get_settings_prompt()
        else:
            full_prompt = base_prompt
        
        # ═══════════════════════════════════════════════════════════════════
        # Adaptive AI Behavior: Adapt prompt to user's cognitive state
        # ═══════════════════════════════════════════════════════════════════
        full_prompt = adaptive_behavior.adapt_system_prompt(
            full_prompt,
            user_kaizen_state,
            kaizen_contours,
        )
        
        # Add emotional context to prompt if detected
        full_prompt = self._add_emotional_context(full_prompt, intent)
        
        # Build context with intent analysis and model role
        context = AgentContext(
            session_id=session_id,
            user_message=user_message,
            history=history,
            memories=memories,
            system_prompt=full_prompt,
            request_type=intent.category.value,
            model_role=model_role.value,  # Hybrid AI: pass selected model role
            user_settings=user_settings,
            db=db,
            user_id=user_id,
            metadata={
                "intent": {
                    "category": intent.category.value,
                    "confidence": intent.confidence,
                    "emotional_state": intent.emotional_state.value,
                    "urgency": intent.urgency,
                    "action_type": intent.action_type.value,
                    "requires_clarification": intent.requires_clarification,
                    "topics": intent.topics,
                },
                "model": {
                    "task_category": task_category.value,
                    "role": model_role.value,
                    "confidence": model_confidence,
                }
            }
        )
        
        # Check if clarification needed
        if intent.requires_clarification and intent.clarification_question:
            return AgentResponse(
                content=intent.clarification_question,
                agent="router",
                save_to_memory=False,
            )
        
        # Select agent
        agent = self.agents.get(intent.category.value, self.default_agent)
        
        logger.info(
            "request_routed",
            category=intent.category.value,
            confidence=intent.confidence,
            emotional_state=intent.emotional_state.value,
            urgency=intent.urgency,
            agent=agent.name,
            model_role=model_role.value,  # Hybrid AI
            session_id=str(session_id),
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
    
    def _add_emotional_context(self, prompt: str, intent: IntentAnalysis) -> str:
        """Add emotional awareness to the system prompt."""
        
        additions = []
        
        # Emotional state hints
        if intent.emotional_state.value == "stressed":
            additions.append(
                "\n\n🚨 Пользователь в стрессе или спешке. "
                "Отвечай кратко и по делу. Избегай длинных ответов."
            )
        elif intent.emotional_state.value == "confused":
            additions.append(
                "\n\n❓ Пользователь кажется растерянным. "
                "Объясняй простым языком, уточняй если нужно."
            )
        elif intent.emotional_state.value == "negative":
            additions.append(
                "\n\n⚠️ Пользователь может быть раздражён. "
                "Проявляй терпение и понимание."
            )
        elif intent.emotional_state.value == "positive":
            additions.append(
                "\n\n✨ Пользователь в хорошем настроении! "
                "Можно быть более творческим в ответах."
            )
        
        # Urgency hint
        if intent.urgency > 0.7:
            additions.append(
                f"\n\n⏰ Срочность: {int(intent.urgency * 100)}%. "
                "Дай ответ максимально быстро и без лишних деталей."
            )
        
        return prompt + "".join(additions)


# Global instance
router = RequestRouter()

