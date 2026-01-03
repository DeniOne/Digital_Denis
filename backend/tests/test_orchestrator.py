"""
Digital Den — Orchestrator Unit Tests
═══════════════════════════════════════════════════════════════════════════

Tests for router.py and context.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

# Import modules under test
import sys
sys.path.insert(0, '.')


class TestRequestRouter:
    """Tests for RequestRouter class."""
    
    @pytest.fixture
    def mock_intent_analyzer(self):
        """Mock intent analyzer."""
        with patch('orchestrator.router.intent_analyzer') as mock:
            # Create a mock IntentAnalysis
            from orchestrator.intent_analyzer import RequestCategory, EmotionalState, ActionType
            mock_analysis = MagicMock()
            mock_analysis.category = RequestCategory.STRATEGIC
            mock_analysis.confidence = 0.9
            mock_analysis.emotional_state = EmotionalState.NEUTRAL
            mock_analysis.urgency = 0.5
            mock_analysis.action_type = ActionType.ANALYZE
            mock_analysis.requires_clarification = False
            mock_analysis.clarification_question = None
            mock_analysis.topics = ["business"]
            
            mock.analyze = AsyncMock(return_value=mock_analysis)
            yield mock
    
    @pytest.fixture
    def mock_short_term(self):
        """Mock short-term memory."""
        with patch('orchestrator.router.short_term_memory') as mock:
            mock.get_chat_history = AsyncMock(return_value=[])
            mock.add_message = AsyncMock()
            yield mock
    
    @pytest.fixture
    def mock_memory_agent(self):
        """Mock memory agent."""
        with patch('orchestrator.router.memory_agent') as mock:
            mock.get_context_memories = AsyncMock(return_value=[])
            mock.save_from_response = AsyncMock()
            yield mock
    
    @pytest.fixture
    def mock_profile(self):
        """Mock profile loader."""
        with patch('orchestrator.router.get_profile') as mock:
            profile = MagicMock()
            profile.get_system_prompt.return_value = "You are Digital Den."
            mock.return_value = profile
            yield mock
    
    @pytest.mark.asyncio
    async def test_route_with_intent_analysis(
        self, 
        mock_intent_analyzer, 
        mock_short_term, 
        mock_memory_agent,
        mock_profile
    ):
        """Test that route uses intent analyzer."""
        from orchestrator.router import RequestRouter
        from agents.base import AgentResponse
        
        with patch('orchestrator.router.core_agent') as mock_agent:
            mock_agent.run = AsyncMock(return_value=AgentResponse(
                content="Test response",
                agent="core",
            ))
            mock_agent.name = "core"
            
            router = RequestRouter()
            response = await router.route("What is our 5-year vision?", session_id=None)
            
            assert response.content == "Test response"
            mock_intent_analyzer.analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_route_creates_session(
        self, 
        mock_intent_analyzer,
        mock_short_term, 
        mock_memory_agent,
        mock_profile
    ):
        """Test that route creates session ID if not provided."""
        from orchestrator.router import RequestRouter
        from agents.base import AgentResponse
        
        with patch('orchestrator.router.core_agent') as mock_agent:
            mock_agent.run = AsyncMock(return_value=AgentResponse(
                content="Test response",
                agent="core",
            ))
            mock_agent.name = "core"
            
            router = RequestRouter()
            response = await router.route("Hello", session_id=None)
            
            assert response.content == "Test response"
            mock_short_term.add_message.assert_called()
    
    @pytest.mark.asyncio
    async def test_route_saves_to_memory(
        self, 
        mock_intent_analyzer,
        mock_short_term, 
        mock_memory_agent,
        mock_profile
    ):
        """Test that route saves to memory when save_to_memory is True."""
        from orchestrator.router import RequestRouter
        from agents.base import AgentResponse
        
        mock_db = MagicMock()
        
        with patch('orchestrator.router.core_agent') as mock_agent:
            mock_agent.run = AsyncMock(return_value=AgentResponse(
                content="Test response",
                agent="core",
                save_to_memory=True,
            ))
            mock_agent.name = "core"
            
            router = RequestRouter()
            response = await router.route("Remember this", session_id=None, db=mock_db)
            
            mock_memory_agent.save_from_response.assert_called()


class TestContextManager:
    """Tests for ContextManager class."""
    
    @pytest.fixture
    def mock_short_term(self):
        """Mock short-term memory."""
        with patch('orchestrator.context.short_term_memory') as mock:
            mock.get_session = AsyncMock(return_value=None)
            mock.save_session = AsyncMock()
            mock.get_chat_history = AsyncMock(return_value=[])
            yield mock
    
    @pytest.fixture
    def mock_long_term(self):
        """Mock long-term memory."""
        with patch('orchestrator.context.long_term_memory') as mock:
            mock.search = AsyncMock(return_value=[])
            yield mock
    
    @pytest.fixture
    def mock_profile(self):
        """Mock profile loader."""
        with patch('orchestrator.context.get_profile') as mock:
            profile = MagicMock()
            profile.get_system_prompt.return_value = "System prompt"
            mock.return_value = profile
            yield mock
    
    @pytest.mark.asyncio
    async def test_get_session_creates_new(self, mock_short_term, mock_profile):
        """Test session creation when none exists."""
        from orchestrator.context import ContextManager
        
        cm = ContextManager()
        session = await cm.get_session("test-session-id")
        
        assert "started_at" in session
        assert "last_activity" in session
        assert session["active_topics"] == []
        mock_short_term.save_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_returns_existing(self, mock_short_term, mock_profile):
        """Test returning existing session."""
        existing_session = {
            "started_at": "2024-01-01T00:00:00",
            "active_topics": ["business"],
        }
        mock_short_term.get_session = AsyncMock(return_value=existing_session)
        
        from orchestrator.context import ContextManager
        
        cm = ContextManager()
        session = await cm.get_session("test-session-id")
        
        assert session["active_topics"] == ["business"]
        mock_short_term.save_session.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_assemble_context(
        self, 
        mock_short_term, 
        mock_long_term, 
        mock_profile
    ):
        """Test full context assembly."""
        from orchestrator.context import ContextManager
        
        cm = ContextManager()
        context = await cm.assemble(
            message="Test message",
            message_type="strategic",
            session_id=uuid4(),
            db=None,
            include_memories=False,
        )
        
        assert context.message == "Test message"
        assert context.message_type == "strategic"
        assert context.system_prompt == "System prompt"
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self, mock_short_term, mock_profile):
        """Test conversation history retrieval."""
        mock_short_term.get_chat_history = AsyncMock(return_value=[
            {"role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:00"},
            {"role": "assistant", "content": "Hi!", "timestamp": "2024-01-01T00:00:01"},
        ])
        
        from orchestrator.context import ContextManager
        
        cm = ContextManager()
        history = await cm.get_conversation_history("test-session")
        
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].role == "assistant"


class TestAgentContext:
    """Tests for AgentContext dataclass."""
    
    def test_agent_context_defaults(self):
        """Test AgentContext default values."""
        from orchestrator.context import AssembledContext
        
        ctx = AssembledContext(
            message="Test",
            message_type="strategic",
        )
        
        assert ctx.message == "Test"
        assert ctx.conversation_history == []
        assert ctx.relevant_memories == []
        assert ctx.active_topics == []
        assert ctx.request_id is not None
        assert ctx.timestamp is not None


# Run with: pytest tests/test_orchestrator.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
