"""
Digital Denis — Memory Layer Unit Tests
═══════════════════════════════════════════════════════════════════════════

Tests for memory layer: short_term, long_term, semantic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

import sys
sys.path.insert(0, '.')


class TestShortTermMemory:
    """Tests for Redis short-term memory."""
    
    @pytest.fixture
    def mock_redis(self):
        with patch('memory.short_term.redis') as mock:
            mock.get = AsyncMock(return_value=None)
            mock.set = AsyncMock()
            mock.lpush = AsyncMock()
            mock.lrange = AsyncMock(return_value=[])
            mock.expire = AsyncMock()
            yield mock
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_redis):
        from memory.short_term import ShortTermMemory
        
        stm = ShortTermMemory()
        session = await stm.get_session("nonexistent")
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_add_message(self, mock_redis):
        from memory.short_term import ShortTermMemory
        
        stm = ShortTermMemory()
        await stm.add_message(
            session_id="test-session",
            role="user",
            content="Hello",
        )
        
        mock_redis.lpush.assert_called()


class TestLongTermMemory:
    """Tests for PostgreSQL long-term memory."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_save_memory_item(self, mock_db):
        from memory.long_term import LongTermMemory
        from memory.models import MemoryItem
        
        ltm = LongTermMemory()
        
        # Mock the result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        item = await ltm.save(
            db=mock_db,
            item_type="decision",
            content="Test decision",
            source_agent="core",
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_by_type(self, mock_db):
        from memory.long_term import LongTermMemory
        
        ltm = LongTermMemory()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        results = await ltm.search(
            db=mock_db,
            query="test",
            item_types=["decision"],
        )
        
        assert results == []


class TestSemanticMemory:
    """Tests for PGVector semantic memory."""
    
    @pytest.fixture
    def mock_openrouter(self):
        with patch('memory.semantic.openrouter') as mock:
            # Return a fake embedding
            mock.get_embedding = AsyncMock(return_value=[0.1] * 1536)
            yield mock
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_get_embedding(self, mock_openrouter):
        from memory.semantic import SemanticMemoryService
        
        service = SemanticMemoryService()
        embedding = await service.get_embedding("Test text")
        
        assert len(embedding) == 1536
        mock_openrouter.get_embedding.assert_called_once_with("Test text")
    
    @pytest.mark.asyncio
    async def test_get_embedding_fallback(self):
        """Test fallback pseudo-embedding when API fails."""
        with patch('memory.semantic.openrouter') as mock:
            mock.get_embedding = AsyncMock(side_effect=Exception("API Error"))
            
            from memory.semantic import SemanticMemoryService
            
            service = SemanticMemoryService()
            embedding = await service.get_embedding("Test")
            
            # Should return pseudo-embedding
            assert len(embedding) == 1536
            assert all(0 <= v <= 1 for v in embedding)
    
    @pytest.mark.asyncio
    async def test_index_memory(self, mock_openrouter, mock_db):
        from memory.semantic import SemanticMemoryService
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        service = SemanticMemoryService()
        success = await service.index(
            db=mock_db,
            memory_id=uuid4(),
            text="Test content",
        )
        
        assert success == True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_embedding_dimension(self):
        from memory.semantic import EMBEDDING_DIMENSION
        
        assert EMBEDDING_DIMENSION == 1536


class TestMemoryModels:
    """Tests for SQLAlchemy models."""
    
    def test_memory_item_creation(self):
        from memory.models import MemoryItem
        
        item = MemoryItem(
            item_type="decision",
            content="Test decision content",
            confidence=0.8,
        )
        
        assert item.item_type == "decision"
        assert item.content == "Test decision content"
        assert item.confidence == 0.8
        assert item.status == "active"
    
    def test_topic_creation(self):
        from memory.models import Topic
        
        topic = Topic(
            name="Business",
            slug="business",
            level=0,
        )
        
        assert topic.name == "Business"
        assert topic.slug == "business"
        assert topic.is_active == True


# Run with: pytest tests/test_memory.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
