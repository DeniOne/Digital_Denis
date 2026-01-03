"""
Digital Den — Memory Layer Unit Tests
═══════════════════════════════════════════════════════════════════════════

Tests for memory layer: short_term, long_term, semantic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime


class TestShortTermMemory:
    """Tests for Redis short-term memory."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = MagicMock()
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock()
        mock.setex = AsyncMock()
        mock.lpush = AsyncMock()
        mock.rpush = AsyncMock()
        mock.lrange = AsyncMock(return_value=[])
        mock.expire = AsyncMock()
        mock.ltrim = AsyncMock()
        return mock
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_redis):
        from memory.short_term import ShortTermMemory
        
        stm = ShortTermMemory()
        stm.redis = mock_redis  # Inject mock redis
        
        session = await stm.get_session("nonexistent")
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_add_message(self, mock_redis):
        from memory.short_term import ShortTermMemory
        
        stm = ShortTermMemory()
        stm.redis = mock_redis  # Inject mock redis
        
        await stm.add_message(
            session_id="test-session",
            role="user",
            content="Hello",
        )
        
        mock_redis.rpush.assert_called()


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
        
        # Mock the result and encryptor
        with patch('memory.long_term.encryptor') as mock_encryptor:
            mock_encryptor.encrypt.side_effect = lambda x: x  # Pass through
            mock_encryptor.decrypt.side_effect = lambda x: x
            
            item = await ltm.save(
                db=mock_db,
                item_type="decision",
                content="Test decision",
                source_agent="core",
            )
            
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_by_text(self, mock_db):
        from memory.long_term import LongTermMemory
        
        ltm = LongTermMemory()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        with patch('memory.long_term.encryptor') as mock_encryptor:
            mock_encryptor.decrypt.side_effect = lambda x: x
            
            # Use query_text, not query
            results = await ltm.search(
                db=mock_db,
                query_text="test",  # Fixed: was 'query'
            )
            
            assert results == []


class TestSemanticMemory:
    """Tests for PGVector semantic memory."""
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Mock the embedding service."""
        with patch('memory.semantic.embedding_service') as mock:
            mock.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
            mock.model = "test-model"
            mock.index_items = AsyncMock(return_value=1)
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
    async def test_get_embedding(self, mock_embedding_service):
        from memory.semantic import SemanticMemoryService
        
        service = SemanticMemoryService()
        embedding = await service.get_embedding("Test text")
        
        assert len(embedding) == 1536
        mock_embedding_service.generate_embedding.assert_called_once_with("Test text")
    
    @pytest.mark.asyncio
    async def test_get_embedding_fallback(self):
        """Test fallback pseudo-embedding when API fails."""
        with patch('memory.semantic.embedding_service') as mock:
            mock.generate_embedding = AsyncMock(side_effect=Exception("API Error"))
            mock.model = "test-model"
            
            from memory.semantic import SemanticMemoryService
            
            service = SemanticMemoryService()
            
            # Should raise an exception since the service doesn't have fallback
            with pytest.raises(Exception):
                await service.get_embedding("Test")
    
    @pytest.mark.asyncio
    async def test_index_memory(self, mock_embedding_service, mock_db):
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
        mock_embedding_service.index_items.assert_called_once()
    
    def test_embedding_dimension(self):
        from memory.models import EMBEDDING_DIMENSION
        
        assert EMBEDDING_DIMENSION == 1536


class TestMemoryModels:
    """Tests for SQLAlchemy models."""
    
    def test_memory_item_creation(self):
        from memory.models import MemoryItem
        
        item = MemoryItem(
            item_type="decision",
            content="Test decision content",
            confidence=0.8,
            status="active",  # Explicitly set since defaults only apply on DB insert
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
            is_active=True,  # Explicitly set since defaults only apply on DB insert
        )
        
        assert topic.name == "Business"
        assert topic.slug == "business"
        assert topic.is_active == True


# Run with: pytest tests/test_memory.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
