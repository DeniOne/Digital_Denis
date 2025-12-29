"""
Digital Denis — CAL Unit Tests
═══════════════════════════════════════════════════════════════════════════

Tests for Cognitive Analytics Layer.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, date

import sys
sys.path.insert(0, '.')


class TestCALService:
    """Tests for CALService class."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        return db
    
    @pytest.fixture
    def mock_topic_extractor(self):
        with patch('analytics.cal_service.topic_extractor') as mock:
            mock.extract = AsyncMock(return_value=[])
            yield mock
    
    @pytest.fixture
    def mock_topic_statistics(self):
        with patch('analytics.cal_service.topic_statistics') as mock:
            mock.get_trends = AsyncMock(return_value=[])
            yield mock


class TestOnMemoryCreated:
    """Tests for on_memory_created hook."""
    
    @pytest.fixture
    def mock_deps(self):
        with patch('analytics.cal_service.topic_extractor') as mock_te, \
             patch('analytics.cal_service.topic_statistics') as mock_ts:
            mock_te.extract = AsyncMock(return_value=[])
            mock_ts.get_trends = AsyncMock(return_value=[])
            yield {"te": mock_te, "ts": mock_ts}
    
    @pytest.mark.asyncio
    async def test_on_memory_created_extracts_topics(self, mock_deps):
        from analytics.cal_service import CALService
        from memory.models import MemoryItem
        
        db = MagicMock()
        
        # Mock the memory item query
        mock_item = MemoryItem(
            id=uuid4(),
            item_type="insight",
            content="Test insight",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_item
        db.execute = AsyncMock(return_value=mock_result)
        db.add = MagicMock()
        db.commit = AsyncMock()
        
        service = CALService()
        await service.on_memory_created(db, mock_item.id)
        
        mock_deps["te"].extract.assert_called()


class TestGetMindMap:
    """Tests for get_mind_map method."""
    
    @pytest.mark.asyncio
    async def test_get_mind_map_returns_graph_data(self):
        from analytics.cal_service import CALService
        
        db = MagicMock()
        
        # Mock empty results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)
        
        service = CALService()
        graph = await service.get_mind_map(db, days=30)
        
        assert graph.nodes == []
        assert graph.edges == []


class TestAnalyzeDecision:
    """Tests for analyze_decision method."""
    
    @pytest.fixture
    def mock_groq(self):
        with patch('analytics.cal_service.groq') as mock:
            mock.complete_simple = AsyncMock(
                return_value='{"strong_points": ["Good"], "weak_points": [], "risks": [], "clarity_score": 0.8, "completeness_score": 0.7, "risk_level": "low", "recommendations": []}'
            )
            yield mock
    
    @pytest.mark.asyncio
    async def test_analyze_decision_creates_analysis(self, mock_groq):
        from analytics.cal_service import CALService
        from memory.models import MemoryItem
        
        db = MagicMock()
        
        # Mock decision
        mock_decision = MemoryItem(
            id=uuid4(),
            item_type="decision",
            content="We will increase budget by 20%",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_decision
        db.execute = AsyncMock(return_value=mock_result)
        db.add = MagicMock()
        
        service = CALService()
        analysis = await service.analyze_decision(db, mock_decision.id)
        
        assert analysis is not None
        assert analysis.risk_level == "low"
        db.add.assert_called()


class TestDetectAnomalies:
    """Tests for detect_anomalies method."""
    
    @pytest.fixture
    def mock_topic_stats(self):
        with patch('analytics.cal_service.topic_statistics') as mock:
            from analytics.topics import TopicTrend
            mock.get_trends = AsyncMock(return_value=[
                TopicTrend(
                    topic_id=uuid4(),
                    topic_name="Finance",
                    current_count=100,
                    previous_count=10,
                    change_percent=900.0,
                    trend="rising",
                )
            ])
            yield mock
    
    @pytest.mark.asyncio
    async def test_detect_anomalies_finds_spikes(self, mock_topic_stats):
        from analytics.cal_service import CALService
        
        db = MagicMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        
        service = CALService()
        anomalies = await service.detect_anomalies(db)
        
        assert len(anomalies) >= 1
        assert anomalies[0].anomaly_type == "topic_spike"


class TestGetCognitiveHealth:
    """Tests for get_cognitive_health method."""
    
    @pytest.mark.asyncio
    async def test_get_cognitive_health_returns_report(self):
        from analytics.cal_service import CALService
        
        db = MagicMock()
        
        # Mock counts
        mock_result = MagicMock()
        mock_result.scalar.return_value = 10
        db.execute = AsyncMock(return_value=mock_result)
        
        service = CALService()
        report = await service.get_cognitive_health(db)
        
        assert report.date == date.today()
        assert hasattr(report, 'overall_score')
        assert hasattr(report, 'recommendations')


class TestCALModels:
    """Tests for CAL database models."""
    
    def test_cal_topic_stats_creation(self):
        from analytics.cal_models import CALTopicStats
        
        stats = CALTopicStats(
            topic_id=uuid4(),
            period_date=date.today(),
            item_count=5,
        )
        
        assert stats.item_count == 5
    
    def test_cal_graph_node_creation(self):
        from analytics.cal_models import CALGraphNode
        
        node = CALGraphNode(
            node_type="decision",
            label="Test decision",
            importance_score=0.8,
        )
        
        assert node.node_type == "decision"
        assert node.importance_score == 0.8
    
    def test_cal_anomaly_creation(self):
        from analytics.cal_models import CALAnomaly
        
        anomaly = CALAnomaly(
            anomaly_type="topic_spike",
            severity="high",
            title="Test anomaly",
            interpretation="Something unusual happened",
        )
        
        assert anomaly.severity == "high"
        assert anomaly.status == "new"


class TestDataClasses:
    """Tests for CAL data classes."""
    
    def test_graph_data(self):
        from analytics.cal_service import GraphData
        
        graph = GraphData(
            nodes=[{"id": "1", "label": "Test"}],
            edges=[{"id": "1", "source": "1", "target": "2"}],
        )
        
        assert len(graph.nodes) == 1
        assert len(graph.edges) == 1
    
    def test_cognitive_health_report(self):
        from analytics.cal_service import CognitiveHealthReport
        
        report = CognitiveHealthReport(
            date=date.today(),
            overall_score=75.0,
            decision_quality=80.0,
            memory_diversity=70.0,
            thinking_consistency=75.0,
            active_topics=10,
            total_memories=100,
            anomalies_count=2,
            recommendations=["Do more reflection"],
        )
        
        assert report.overall_score == 75.0


# Run with: pytest tests/test_cal.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
