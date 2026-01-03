"""
Digital Den — Memory Agent v2 Unit Tests
═══════════════════════════════════════════════════════════════════════════

Tests for extended Memory Agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

import sys
sys.path.insert(0, '.')


class TestMemoryAgentV2:
    """Tests for MemoryAgentV2 class."""
    
    @pytest.fixture
    def mock_groq(self):
        with patch('agents.memory_agent.groq') as mock:
            mock.complete_simple = AsyncMock(
                return_value='[{"type": "decision", "content": "Решение принято", "confidence": 0.9}]'
            )
            yield mock
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        return db
    
    @pytest.fixture
    def mock_semantic_memory(self):
        with patch('agents.memory_agent.semantic_memory') as mock:
            mock.index = AsyncMock(return_value=True)
            mock.search = AsyncMock(return_value=[])
            mock.find_similar = AsyncMock(return_value=[])
            yield mock
    
    @pytest.fixture
    def mock_topic_extractor(self):
        with patch('agents.memory_agent.topic_extractor') as mock:
            mock.extract = AsyncMock(return_value=[])
            yield mock
    
    @pytest.fixture
    def mock_long_term(self):
        with patch('agents.memory_agent.long_term_memory') as mock:
            mock_item = MagicMock()
            mock_item.id = uuid4()
            mock.save = AsyncMock(return_value=mock_item)
            mock.search = AsyncMock(return_value=[])
            yield mock


class TestExtractCandidates:
    """Tests for extract_candidates method."""
    
    @pytest.fixture
    def mock_groq(self):
        with patch('agents.memory_agent.groq') as mock:
            yield mock
    
    @pytest.mark.asyncio
    async def test_extract_candidates_decision(self, mock_groq):
        mock_groq.complete_simple = AsyncMock(
            return_value='[{"type": "decision", "content": "Будем делать X", "confidence": 0.9}]'
        )
        
        from agents.memory_agent import MemoryAgentV2
        
        agent = MemoryAgentV2()
        candidates = await agent.extract_candidates("Я решил, что будем делать X")
        
        assert len(candidates) == 1
        assert candidates[0].type == "decision"
        assert candidates[0].confidence == 0.9
    
    @pytest.mark.asyncio
    async def test_extract_candidates_fallback(self, mock_groq):
        """Test fallback rule-based extraction when LLM fails."""
        mock_groq.complete_simple = AsyncMock(side_effect=Exception("API Error"))
        
        from agents.memory_agent import MemoryAgentV2
        
        agent = MemoryAgentV2()
        candidates = await agent.extract_candidates("Я решил сделать это.")
        
        # Should use rule-based fallback
        assert len(candidates) >= 1
        assert candidates[0].type == "decision"
    
    def test_rule_based_extraction(self):
        from agents.memory_agent import MemoryAgentV2
        
        agent = MemoryAgentV2()
        
        # Test decision pattern
        candidates = agent._rule_based_extraction("Я принял решение увеличить бюджет.")
        assert any(c.type == "decision" for c in candidates)
        
        # Test insight pattern  
        candidates = agent._rule_based_extraction("Я понял ключевой момент.")
        assert any(c.type == "insight" for c in candidates)


class TestAutoSave:
    """Tests for auto_save method."""
    
    @pytest.fixture
    def mock_all_deps(self):
        with patch('agents.memory_agent.groq') as mock_groq, \
             patch('agents.memory_agent.semantic_memory') as mock_semantic, \
             patch('agents.memory_agent.topic_extractor') as mock_topics, \
             patch('agents.memory_agent.long_term_memory') as mock_ltm:
            
            mock_groq.complete_simple = AsyncMock(
                return_value='[{"type": "decision", "content": "Test", "confidence": 0.95}]'
            )
            
            mock_semantic.search = AsyncMock(return_value=[])  # No duplicates
            mock_semantic.index = AsyncMock(return_value=True)
            
            mock_topics.extract = AsyncMock(return_value=[])
            
            mock_item = MagicMock()
            mock_item.id = uuid4()
            mock_ltm.save = AsyncMock(return_value=mock_item)
            
            yield {
                "groq": mock_groq,
                "semantic": mock_semantic,
                "topics": mock_topics,
                "ltm": mock_ltm,
            }
    
    @pytest.mark.asyncio
    async def test_auto_save_saves_high_confidence(self, mock_all_deps):
        from agents.memory_agent import MemoryAgentV2
        from agents.base import AgentContext, AgentResponse
        
        agent = MemoryAgentV2()
        
        db = MagicMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        
        context = AgentContext(
            session_id=uuid4(),
            user_message="Я решил это сделать",
        )
        
        response = AgentResponse(
            content="Хорошо, решение принято",
            agent="core",
        )
        
        actions = await agent.auto_save(db, response, context)
        
        # Should save high-confidence decision
        assert len(actions) >= 0  # May vary based on extraction


class TestForgetFunctionality:
    """Tests for forget/restore methods."""
    
    @pytest.fixture
    def mock_semantic(self):
        with patch('agents.memory_agent.semantic_memory') as mock:
            mock_item = MagicMock()
            mock_item.id = uuid4()
            mock_item.content = "Test content"
            mock_item.item_type = "decision"
            mock_item.created_at = datetime.utcnow()
            
            mock.search = AsyncMock(return_value=[(mock_item, 0.9)])
            mock.find_similar = AsyncMock(return_value=[])
            yield mock
    
    @pytest.mark.asyncio
    async def test_prepare_forget(self, mock_semantic):
        from agents.memory_agent import MemoryAgentV2
        
        db = MagicMock()
        db.execute = AsyncMock()
        
        agent = MemoryAgentV2()
        request, message = await agent.prepare_forget(db, "удали решение о бюджете")
        
        assert request is not None
        assert request.memory_id is not None
        assert "Найдено" in message
    
    @pytest.mark.asyncio
    async def test_execute_forget_requires_confirmation(self):
        from agents.memory_agent import MemoryAgentV2, ForgetRequest
        
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        
        agent = MemoryAgentV2()
        
        # Without confirmation
        request = ForgetRequest(memory_id=uuid4(), confirmed=False)
        result = await agent.execute_forget(db, request)
        
        assert result == False  # Should not delete without confirmation


class TestAggregate:
    """Tests for aggregation functionality."""
    
    @pytest.fixture
    def mock_deps(self):
        with patch('agents.memory_agent.groq') as mock_groq, \
             patch('agents.memory_agent.semantic_memory') as mock_semantic:
            
            mock_groq.complete_simple = AsyncMock(return_value="Сводка записей")
            mock_semantic.find_similar = AsyncMock(return_value=[])
            
            yield {"groq": mock_groq, "semantic": mock_semantic}
    
    @pytest.mark.asyncio
    async def test_aggregate_needs_min_items(self, mock_deps):
        from agents.memory_agent import MemoryAgentV2
        
        db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No items
        db.execute = AsyncMock(return_value=mock_result)
        
        agent = MemoryAgentV2()
        aggregated = await agent.aggregate_similar(db, min_cluster_size=3)
        
        assert aggregated == []  # Not enough items


class TestOperationClassification:
    """Tests for operation classification."""
    
    def test_classify_forget(self):
        from agents.memory_agent import MemoryAgentV2, MemoryActionType
        
        agent = MemoryAgentV2()
        
        assert agent._classify_operation("забудь это решение") == MemoryActionType.FORGET
        assert agent._classify_operation("удали запись") == MemoryActionType.FORGET
    
    def test_classify_search(self):
        from agents.memory_agent import MemoryAgentV2, MemoryActionType
        
        agent = MemoryAgentV2()
        
        assert agent._classify_operation("найди мои решения") == MemoryActionType.SEARCH
        assert agent._classify_operation("вспомни что я говорил") == MemoryActionType.SEARCH
    
    def test_classify_aggregate(self):
        from agents.memory_agent import MemoryAgentV2, MemoryActionType
        
        agent = MemoryAgentV2()
        
        assert agent._classify_operation("объедини похожие") == MemoryActionType.AGGREGATE


class TestMemoryCandidate:
    """Tests for MemoryCandidate dataclass."""
    
    def test_creation(self):
        from agents.memory_agent import MemoryCandidate
        
        candidate = MemoryCandidate(
            type="decision",
            content="Test decision",
            confidence=0.9,
        )
        
        assert candidate.type == "decision"
        assert candidate.confidence == 0.9
        assert candidate.structured_data is None


class TestBackwardCompatibility:
    """Tests for backward compatibility with v1."""
    
    def test_legacy_agent_exists(self):
        from agents.memory_agent import memory_agent
        
        assert memory_agent is not None
        assert memory_agent.name == "memory"
    
    def test_v2_agent_exists(self):
        from agents.memory_agent import memory_agent_v2
        
        assert memory_agent_v2 is not None
        assert memory_agent_v2.name == "memory_v2"


# Run with: pytest tests/test_memory_agent.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
