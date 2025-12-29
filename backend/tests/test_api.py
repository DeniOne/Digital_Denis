"""
Digital Denis — API Tests
═══════════════════════════════════════════════════════════════════════════

Integration tests for API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

import sys
sys.path.insert(0, '.')


class TestMessagesAPI:
    """Tests for Messages API."""
    
    def test_message_request_schema(self):
        from api.routes.messages import MessageRequest
        
        req = MessageRequest(content="Hello")
        assert req.content == "Hello"


class TestMemoryAPI:
    """Tests for Memory API."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        return db
    
    def test_memory_item_schema(self):
        from api.routes.memory import MemoryItemSchema
        
        item = MemoryItemSchema(
            id=uuid4(),
            item_type="decision",
            content="Test decision",
            created_at="2024-01-01T00:00:00",
            status="active",
        )
        
        assert item.item_type == "decision"


class TestHealthAPI:
    """Tests for Health API."""
    
    @pytest.mark.asyncio
    async def test_ping(self):
        from api.routes.health import ping
        
        result = await ping()
        
        assert result["status"] == "pong"
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_liveness(self):
        from api.routes.health import liveness_check
        
        result = await liveness_check()
        
        assert result["alive"] == True


class TestTopicsAPI:
    """Tests for Topics API."""
    
    def test_router_exists(self):
        from api.routes.topics import router
        
        assert router is not None


class TestMindmapAPI:
    """Tests for Mindmap API."""
    
    def test_router_exists(self):
        from api.routes.mindmap import router
        
        assert router is not None


class TestDecisionsAPI:
    """Tests for Decisions API."""
    
    def test_router_exists(self):
        from api.routes.decisions import router
        
        assert router is not None


class TestAnomaliesAPI:
    """Tests for Anomalies API."""
    
    def test_router_exists(self):
        from api.routes.anomalies import router
        
        assert router is not None


class TestCALAPI:
    """Tests for CAL API."""
    
    def test_router_exists(self):
        from api.routes.cal import router
        
        assert router is not None


class TestUnifiedRouter:
    """Tests for unified API router."""
    
    def test_api_router_exists(self):
        from api.routes import api_router
        
        assert api_router is not None
        assert api_router.prefix == "/api/v1"


# Run with: pytest tests/test_api.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
