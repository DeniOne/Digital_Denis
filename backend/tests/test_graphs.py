"""
Digital Den — Mind Map Graph Unit Tests
═══════════════════════════════════════════════════════════════════════════

Tests for graphs.py and mind map functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

import sys
sys.path.insert(0, '.')


class TestGraphBuilder:
    """Tests for GraphBuilder class."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        return db
    
    @pytest.fixture
    def mock_semantic(self):
        with patch('analytics.graphs.semantic_memory') as mock:
            mock.search = AsyncMock(return_value=[])
            yield mock
    
    @pytest.fixture
    def mock_groq(self):
        with patch('analytics.graphs.groq') as mock:
            mock.complete_simple = AsyncMock(return_value="relates_to")
            yield mock


class TestCreateNodeFromMemory:
    """Tests for create_node_from_memory method."""
    
    @pytest.mark.asyncio
    async def test_create_node_from_decision(self):
        from analytics.graphs import GraphBuilder
        from memory.models import MemoryItem
        
        db = MagicMock()
        db.add = MagicMock()
        
        builder = GraphBuilder()
        
        memory = MemoryItem(
            id=uuid4(),
            item_type="decision",
            content="We will increase budget",
            summary="Budget increase decision",
            confidence=0.9,
        )
        
        node = await builder.create_node_from_memory(db, memory)
        
        assert node.node_type == "decision"
        assert node.label == "Budget increase decision"
        assert node.importance_score > 0.5  # Decisions have higher importance
        db.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_node_from_insight(self):
        from analytics.graphs import GraphBuilder
        from memory.models import MemoryItem
        
        db = MagicMock()
        db.add = MagicMock()
        
        builder = GraphBuilder()
        
        memory = MemoryItem(
            id=uuid4(),
            item_type="insight",
            content="Key insight about process",
        )
        
        node = await builder.create_node_from_memory(db, memory)
        
        assert node.node_type == "insight"


class TestDetermineEdgeType:
    """Tests for _determine_edge_type method."""
    
    @pytest.fixture
    def mock_groq(self):
        with patch('analytics.graphs.groq') as mock:
            yield mock
    
    @pytest.mark.asyncio
    async def test_determine_edge_type_depends_on(self, mock_groq):
        mock_groq.complete_simple = AsyncMock(return_value="depends_on")
        
        from analytics.graphs import GraphBuilder
        from memory.models import MemoryItem
        
        builder = GraphBuilder()
        
        source = MemoryItem(id=uuid4(), item_type="decision", content="Build feature X")
        target = MemoryItem(id=uuid4(), item_type="decision", content="Hire developers")
        
        edge_type = await builder._determine_edge_type(source, target)
        
        assert edge_type == "depends_on"
    
    @pytest.mark.asyncio
    async def test_determine_edge_type_none(self, mock_groq):
        mock_groq.complete_simple = AsyncMock(return_value="none")
        
        from analytics.graphs import GraphBuilder
        from memory.models import MemoryItem
        
        builder = GraphBuilder()
        
        source = MemoryItem(id=uuid4(), item_type="fact", content="Sky is blue")
        target = MemoryItem(id=uuid4(), item_type="fact", content="Water is wet")
        
        edge_type = await builder._determine_edge_type(source, target)
        
        assert edge_type is None


class TestCheckContradiction:
    """Tests for _check_contradiction method."""
    
    @pytest.fixture
    def mock_groq(self):
        with patch('analytics.graphs.groq') as mock:
            yield mock
    
    @pytest.mark.asyncio
    async def test_contradiction_detected(self, mock_groq):
        mock_groq.complete_simple = AsyncMock(return_value="YES 0.85")
        
        from analytics.graphs import GraphBuilder
        from memory.models import MemoryItem
        
        builder = GraphBuilder()
        
        a = MemoryItem(id=uuid4(), item_type="decision", content="Increase spending")
        b = MemoryItem(id=uuid4(), item_type="decision", content="Cut all costs")
        
        is_contra, score = await builder._check_contradiction(a, b)
        
        assert is_contra == True
        assert score == 0.85
    
    @pytest.mark.asyncio
    async def test_no_contradiction(self, mock_groq):
        mock_groq.complete_simple = AsyncMock(return_value="NO 0.9")
        
        from analytics.graphs import GraphBuilder
        from memory.models import MemoryItem
        
        builder = GraphBuilder()
        
        a = MemoryItem(id=uuid4(), item_type="decision", content="Hire more")
        b = MemoryItem(id=uuid4(), item_type="decision", content="Train team")
        
        is_contra, score = await builder._check_contradiction(a, b)
        
        assert is_contra == False


class TestMindMapService:
    """Tests for MindMapService class."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_get_graph_returns_data(self, mock_db):
        from analytics.graphs import MindMapService
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        service = MindMapService()
        graph = await service.get_graph(mock_db, days=30)
        
        assert graph.nodes == []
        assert graph.edges == []
        assert "total_nodes" in graph.metadata


class TestNodeTypes:
    """Tests for node type enums and colors."""
    
    def test_node_types_defined(self):
        from analytics.graphs import NodeType
        
        assert NodeType.IDEA.value == "idea"
        assert NodeType.DECISION.value == "decision"
        assert NodeType.INSIGHT.value == "insight"
    
    def test_edge_types_defined(self):
        from analytics.graphs import EdgeType
        
        assert EdgeType.DEPENDS_ON.value == "depends_on"
        assert EdgeType.CONTRADICTS.value == "contradicts"
        assert EdgeType.REINFORCES.value == "reinforces"
    
    def test_node_colors_defined(self):
        from analytics.graphs import NODE_COLORS, NodeType
        
        assert NodeType.DECISION in NODE_COLORS
        assert NODE_COLORS[NodeType.DECISION].startswith("#")
    
    def test_edge_styles_defined(self):
        from analytics.graphs import EDGE_STYLES, EdgeType
        
        assert EdgeType.CONTRADICTS in EDGE_STYLES
        assert EDGE_STYLES[EdgeType.CONTRADICTS]["style"] == "dashed"


class TestDataClasses:
    """Tests for graph data classes."""
    
    def test_graph_node_creation(self):
        from analytics.graphs import GraphNode
        
        node = GraphNode(
            id="123",
            label="Test node",
            node_type="decision",
            size=1.5,
            color="#27AE60",
        )
        
        assert node.id == "123"
        assert node.node_type == "decision"
    
    def test_graph_edge_creation(self):
        from analytics.graphs import GraphEdge
        
        edge = GraphEdge(
            id="456",
            source="123",
            target="789",
            edge_type="depends_on",
            weight=0.85,
            style="solid",
            color="#4A90A4",
        )
        
        assert edge.source == "123"
        assert edge.target == "789"
    
    def test_graph_data_creation(self):
        from analytics.graphs import GraphData, GraphNode, GraphEdge
        
        node = GraphNode(id="1", label="A", node_type="idea")
        edge = GraphEdge(id="e1", source="1", target="2", edge_type="relates_to")
        
        graph = GraphData(nodes=[node], edges=[edge])
        
        assert len(graph.nodes) == 1
        assert len(graph.edges) == 1


# Run with: pytest tests/test_graphs.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
