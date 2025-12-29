"""
Digital Denis — Anomaly Detection Unit Tests
═══════════════════════════════════════════════════════════════════════════

Tests for anomalies.py and AnomalyDetector.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, date

import sys
sys.path.insert(0, '.')


class TestAnomalyDetector:
    """Tests for AnomalyDetector class."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        return db


class TestCheckTopics:
    """Tests for topic anomaly detection."""
    
    def test_detects_topic_spike(self):
        from analytics.anomalies import AnomalyDetector, Baseline, CurrentMetrics
        
        detector = AnomalyDetector()
        
        topic_id = uuid4()
        baseline = Baseline(
            period_days=30,
            topic_frequencies={topic_id: 10.0},
            topic_names={topic_id: "Finance"},
        )
        
        current = CurrentMetrics(
            period_days=7,
            topic_frequencies={topic_id: 10.0},  # 10 in 7 days vs 10 in 30 days = huge spike
        )
        
        anomalies = detector._check_topics(baseline, current)
        
        assert len(anomalies) >= 1
        spike = [a for a in anomalies if a.anomaly_type.value == "topic_spike"]
        assert len(spike) == 1
    
    def test_detects_topic_disappearance(self):
        from analytics.anomalies import AnomalyDetector, Baseline, CurrentMetrics
        
        detector = AnomalyDetector()
        
        topic_id = uuid4()
        baseline = Baseline(
            period_days=30,
            topic_frequencies={topic_id: 100.0},
            topic_names={topic_id: "Important Topic"},
        )
        
        current = CurrentMetrics(
            period_days=7,
            topic_frequencies={topic_id: 1.0},  # Barely any activity
        )
        
        anomalies = detector._check_topics(baseline, current)
        
        drop = [a for a in anomalies if a.anomaly_type.value == "topic_disappearance"]
        assert len(drop) == 1


class TestCheckDecisions:
    """Tests for decision rate anomaly detection."""
    
    def test_detects_decision_surge(self):
        from analytics.anomalies import AnomalyDetector, Baseline, CurrentMetrics
        
        detector = AnomalyDetector()
        
        baseline = Baseline(
            period_days=30,
            decision_count=30,  # 30 in 30 days = 1/day = 7/week
        )
        
        current = CurrentMetrics(
            period_days=7,
            decision_count=20,  # 20 in 7 days = ~2.8/day = much higher
        )
        
        anomalies = detector._check_decisions(baseline, current)
        
        surge = [a for a in anomalies if a.anomaly_type.value == "decision_surge"]
        assert len(surge) >= 1
    
    def test_detects_decision_drought(self):
        from analytics.anomalies import AnomalyDetector, Baseline, CurrentMetrics
        
        detector = AnomalyDetector()
        
        baseline = Baseline(
            period_days=30,
            decision_count=60,  # 2/day = 14/week
        )
        
        current = CurrentMetrics(
            period_days=7,
            decision_count=2,  # Only 2 in 7 days
        )
        
        anomalies = detector._check_decisions(baseline, current)
        
        drought = [a for a in anomalies if a.anomaly_type.value == "decision_drought"]
        assert len(drought) >= 1


class TestCheckConfidence:
    """Tests for confidence anomaly detection."""
    
    def test_detects_confidence_spike(self):
        from analytics.anomalies import AnomalyDetector, Baseline, CurrentMetrics
        
        detector = AnomalyDetector()
        
        baseline = Baseline(
            period_days=30,
            avg_confidence=0.6,
        )
        
        current = CurrentMetrics(
            period_days=7,
            avg_confidence=0.9,  # +50%
        )
        
        anomalies = detector._check_confidence(baseline, current)
        
        spike = [a for a in anomalies if a.anomaly_type.value == "confidence_spike"]
        assert len(spike) == 1
    
    def test_detects_confidence_drop(self):
        from analytics.anomalies import AnomalyDetector, Baseline, CurrentMetrics
        
        detector = AnomalyDetector()
        
        baseline = Baseline(
            period_days=30,
            avg_confidence=0.8,
        )
        
        current = CurrentMetrics(
            period_days=7,
            avg_confidence=0.5,  # -37.5%
        )
        
        anomalies = detector._check_confidence(baseline, current)
        
        drop = [a for a in anomalies if a.anomaly_type.value == "confidence_drop"]
        assert len(drop) == 1


class TestCheckTopicDiversity:
    """Tests for topic diversity anomaly detection."""
    
    def test_detects_topic_narrowing(self):
        from analytics.anomalies import AnomalyDetector, CurrentMetrics
        
        detector = AnomalyDetector()
        
        current = CurrentMetrics(
            period_days=7,
            active_topics=2,  # Below threshold of 3
        )
        
        anomalies = detector._check_topic_diversity(current)
        
        narrowing = [a for a in anomalies if a.anomaly_type.value == "topic_narrowing"]
        assert len(narrowing) == 1
    
    def test_no_anomaly_with_diverse_topics(self):
        from analytics.anomalies import AnomalyDetector, CurrentMetrics
        
        detector = AnomalyDetector()
        
        current = CurrentMetrics(
            period_days=7,
            active_topics=5,  # Above threshold
        )
        
        anomalies = detector._check_topic_diversity(current)
        
        assert len(anomalies) == 0


class TestAnomalyService:
    """Tests for AnomalyService class."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_acknowledge_anomaly(self, mock_db):
        from analytics.anomalies import AnomalyService
        from analytics.cal_models import CALAnomaly
        
        mock_anomaly = CALAnomaly(
            id=uuid4(),
            anomaly_type="topic_spike",
            severity="medium",
            status="new",
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_anomaly
        mock_db.execute.return_value = mock_result
        
        service = AnomalyService()
        result = await service.acknowledge(mock_db, mock_anomaly.id)
        
        assert result == True
        assert mock_anomaly.status == "acknowledged"
    
    @pytest.mark.asyncio
    async def test_get_stats(self, mock_db):
        from analytics.anomalies import AnomalyService
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result
        
        service = AnomalyService()
        stats = await service.get_stats(mock_db)
        
        assert "by_status" in stats
        assert "new_last_7_days" in stats


class TestDataClasses:
    """Tests for data classes."""
    
    def test_baseline_creation(self):
        from analytics.anomalies import Baseline
        
        baseline = Baseline(
            period_days=30,
            decision_count=10,
            avg_confidence=0.75,
        )
        
        assert baseline.period_days == 30
        assert baseline.topic_frequencies == {}  # Default
    
    def test_current_metrics_creation(self):
        from analytics.anomalies import CurrentMetrics
        
        current = CurrentMetrics(
            period_days=7,
            active_topics=5,
        )
        
        assert current.period_days == 7
    
    def test_anomaly_creation(self):
        from analytics.anomalies import Anomaly, AnomalyType, Severity
        
        anomaly = Anomaly(
            anomaly_type=AnomalyType.TOPIC_SPIKE,
            severity=Severity.MEDIUM,
            title="Test",
            description="Test description",
            deviation_percent=55.0,
        )
        
        assert anomaly.anomaly_type == AnomalyType.TOPIC_SPIKE
        assert anomaly.deviation_percent == 55.0


class TestInterpret:
    """Tests for LLM interpretation."""
    
    @pytest.fixture
    def mock_groq(self):
        with patch('analytics.anomalies.groq') as mock:
            mock.complete_simple = AsyncMock(
                return_value="Это может указывать на повышенный интерес к теме."
            )
            yield mock
    
    @pytest.mark.asyncio
    async def test_interpret_anomaly(self, mock_groq):
        from analytics.anomalies import AnomalyDetector, Anomaly, AnomalyType, Severity
        
        detector = AnomalyDetector()
        
        anomaly = Anomaly(
            anomaly_type=AnomalyType.TOPIC_SPIKE,
            severity=Severity.MEDIUM,
            title="Test",
            description="Test",
            deviation_percent=60.0,
        )
        
        interpretation = await detector._interpret(anomaly)
        
        assert len(interpretation) > 0
        mock_groq.complete_simple.assert_called_once()


# Run with: pytest tests/test_anomalies.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
