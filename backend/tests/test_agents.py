"""
Digital Den — Agent Unit Tests
═══════════════════════════════════════════════════════════════════════════

Tests for all agent implementations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

import sys
sys.path.insert(0, '.')


class TestCoreAgent:
    """Tests for CoreAgent."""
    
    @pytest.fixture
    def mock_openrouter(self):
        with patch('agents.core_agent.openrouter') as mock:
            response = MagicMock()
            response.content = "Test response"
            response.tokens_used = 100
            mock.complete = AsyncMock(return_value=response)
            yield mock
    
    @pytest.mark.asyncio
    async def test_process_returns_response(self, mock_openrouter):
        from agents.core_agent import CoreAgent
        from agents.base import AgentContext
        
        agent = CoreAgent()
        context = AgentContext(
            session_id=uuid4(),
            user_message="Test message",
            system_prompt="You are helpful.",
        )
        
        response = await agent.process(context)
        
        assert response.content == "Test response"
        assert response.agent == "core"
        mock_openrouter.complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_should_save_decision(self, mock_openrouter):
        from agents.core_agent import CoreAgent
        
        agent = CoreAgent()
        
        # Test decision detection
        should_save, mem_type = agent._should_save(
            "Я принял решение",
            "Хорошо, решение зафиксировано"
        )
        assert should_save == True
        assert mem_type == "decision"
    
    @pytest.mark.asyncio
    async def test_should_save_insight(self, mock_openrouter):
        from agents.core_agent import CoreAgent
        
        agent = CoreAgent()
        
        should_save, mem_type = agent._should_save(
            "Я понял важный момент",
            "Этот инсайт ценен"
        )
        assert should_save == True
        assert mem_type == "insight"


class TestAnalystAgent:
    """Tests for AnalystAgent."""
    
    @pytest.fixture
    def mock_openrouter(self):
        with patch('agents.analyst_agent.openrouter') as mock:
            response = MagicMock()
            response.content = "## Выводы\nКлючевой вывод: данные показывают..."
            response.tokens_used = 150
            mock.complete = AsyncMock(return_value=response)
            yield mock
    
    @pytest.mark.asyncio
    async def test_process_analytical_request(self, mock_openrouter):
        from agents.analyst_agent import AnalystAgent
        from agents.base import AgentContext
        
        agent = AnalystAgent()
        context = AgentContext(
            session_id=uuid4(),
            user_message="Проанализируй конверсию",
            system_prompt="System prompt",
        )
        
        response = await agent.process(context)
        
        assert response.agent == "analyst"
        assert response.save_to_memory == True  # Contains "Выводы"
    
    def test_analyze_for_insights(self):
        from agents.analyst_agent import AnalystAgent
        
        agent = AnalystAgent()
        
        # Test insight detection
        save, mem_type = agent._analyze_for_insights("Ключевой вывод: тренд растущий")
        assert save == True
        assert mem_type == "insight"


class TestOperatorAgent:
    """Tests for OperatorAgent."""
    
    @pytest.fixture
    def mock_openrouter(self):
        with patch('agents.operator_agent.openrouter') as mock:
            response = MagicMock()
            response.content = "## План действий\n- [ ] Шаг 1\n- [ ] Шаг 2"
            response.tokens_used = 120
            mock.complete = AsyncMock(return_value=response)
            yield mock
    
    @pytest.mark.asyncio
    async def test_process_operational_request(self, mock_openrouter):
        from agents.operator_agent import OperatorAgent
        from agents.base import AgentContext
        
        agent = OperatorAgent()
        context = AgentContext(
            session_id=uuid4(),
            user_message="Составь план внедрения",
            system_prompt="System prompt",
        )
        
        response = await agent.process(context)
        
        assert response.agent == "operator"
        assert response.save_to_memory == True  # Contains checklist
    
    def test_is_actionable_plan(self):
        from agents.operator_agent import OperatorAgent
        
        agent = OperatorAgent()
        
        # Checklist format
        assert agent._is_actionable_plan("- [ ] Задача 1") == True
        
        # Table format
        assert agent._is_actionable_plan("| Этап | Задача |") == True
        
        # Plain text (not a plan)
        assert agent._is_actionable_plan("Просто текст без плана") == False


class TestMetaAnalystAgent:
    """Tests for MetaAnalystAgent."""
    
    @pytest.fixture
    def mock_openrouter(self):
        with patch('agents.meta_analyst.openrouter') as mock:
            response = MagicMock()
            response.content = "## Ключевые темы\n- Бизнес (тренд: up)"
            response.tokens_used = 200
            mock.complete = AsyncMock(return_value=response)
            yield mock
    
    def test_meta_analyst_not_in_dialogue(self):
        from agents.meta_analyst import MetaAnalystAgent
        
        agent = MetaAnalystAgent()
        
        assert agent.participates_in_dialogue == False
        assert agent.is_synchronous == False
    
    @pytest.mark.asyncio
    async def test_analyze_period(self, mock_openrouter):
        from agents.meta_analyst import MetaAnalystAgent
        
        agent = MetaAnalystAgent()
        memories = [
            {"item_type": "decision", "content": "Решение 1", "created_at": "2024-01-01"},
            {"item_type": "insight", "content": "Инсайт 1", "created_at": "2024-01-02"},
        ]
        
        report = await agent.analyze_period(memories, period_days=7)
        
        assert report.report_type.value == "weekly_summary"
        assert "Ключевые темы" in report.content
    
    @pytest.mark.asyncio
    async def test_analyze_period_no_data(self, mock_openrouter):
        from agents.meta_analyst import MetaAnalystAgent
        
        agent = MetaAnalystAgent()
        
        report = await agent.analyze_period([], period_days=7)
        
        assert report.priority == "low"
        assert "Недостаточно данных" in report.content


class TestBaseAgent:
    """Tests for BaseAgent interface."""
    
    def test_agent_context_defaults(self):
        from agents.base import AgentContext
        
        ctx = AgentContext(
            session_id=uuid4(),
            user_message="Test",
        )
        
        assert ctx.history == []
        assert ctx.memories == []
        assert ctx.system_prompt == ""
    
    def test_agent_response_defaults(self):
        from agents.base import AgentResponse
        
        resp = AgentResponse(
            content="Response",
            agent="test",
        )
        
        assert resp.save_to_memory == False
        assert resp.confidence == 0.5
        assert resp.follow_up is None


# Run with: pytest tests/test_agents.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
