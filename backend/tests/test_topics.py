"""
Digital Den — Topic Intelligence Unit Tests
═══════════════════════════════════════════════════════════════════════════

Tests for topics.py and topic extraction.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

import sys
sys.path.insert(0, '.')


class TestTopicExtractor:
    """Tests for TopicExtractor class."""
    
    @pytest.fixture
    def mock_groq(self):
        with patch('analytics.topics.groq') as mock:
            mock.complete_simple = AsyncMock(
                return_value='[{"topic": "finance", "confidence": 0.85}]'
            )
            yield mock
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_extract_topics(self, mock_groq):
        from analytics.topics import TopicExtractor, TopicTree
        from memory.models import Topic
        
        extractor = TopicExtractor()
        
        # Setup mock topic tree
        mock_topic = Topic(
            id=uuid4(),
            name="Finance",
            slug="finance",
        )
        extractor.topic_tree.topics = {"finance": mock_topic}
        
        assignments = await extractor.extract("Обсуждаем бюджет на следующий год")
        
        assert len(assignments) == 1
        assert assignments[0].topic_slug == "finance"
        assert assignments[0].confidence == 0.85
    
    @pytest.mark.asyncio
    async def test_extract_filters_low_confidence(self, mock_groq):
        mock_groq.complete_simple = AsyncMock(
            return_value='[{"topic": "finance", "confidence": 0.3}]'
        )
        
        from analytics.topics import TopicExtractor
        from memory.models import Topic
        
        extractor = TopicExtractor(min_confidence=0.5)
        extractor.topic_tree.topics = {
            "finance": Topic(id=uuid4(), name="Finance", slug="finance")
        }
        
        assignments = await extractor.extract("Text")
        
        assert len(assignments) == 0  # Filtered out due to low confidence
    
    def test_parse_response_valid_json(self):
        from analytics.topics import TopicExtractor
        
        extractor = TopicExtractor()
        
        response = '[{"topic": "hr", "confidence": 0.9}, {"topic": "finance", "confidence": 0.7}]'
        assignments = extractor._parse_response(response)
        
        assert len(assignments) == 2
        assert assignments[0].topic_slug == "hr"
        assert assignments[1].topic_slug == "finance"
    
    def test_parse_response_invalid_json(self):
        from analytics.topics import TopicExtractor
        
        extractor = TopicExtractor()
        
        response = "not valid json"
        assignments = extractor._parse_response(response)
        
        assert len(assignments) == 0


class TestTopicTree:
    """Tests for TopicTree class."""
    
    def test_exists(self):
        from analytics.topics import TopicTree
        from memory.models import Topic
        
        tree = TopicTree()
        tree.topics = {
            "finance": Topic(id=uuid4(), name="Finance", slug="finance"),
            "hr": Topic(id=uuid4(), name="HR", slug="hr"),
        }
        
        assert tree.exists("finance") == True
        assert tree.exists("nonexistent") == False
    
    def test_get(self):
        from analytics.topics import TopicTree
        from memory.models import Topic
        
        tree = TopicTree()
        topic = Topic(id=uuid4(), name="Finance", slug="finance")
        tree.topics = {"finance": topic}
        
        result = tree.get("finance")
        assert result == topic
        
        result = tree.get("nonexistent")
        assert result is None


class TestTopicStatistics:
    """Tests for TopicStatistics class."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_get_activity(self, mock_db):
        from analytics.topics import TopicStatistics
        
        # Mock result
        mock_row = MagicMock()
        mock_row.topic_id = uuid4()
        mock_row.topic_name = "Finance"
        mock_row.item_count = 10
        mock_row.decision_count = 3
        mock_row.insight_count = 5
        mock_row.avg_confidence = 0.75
        mock_row.last_activity = datetime.utcnow()
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_db.execute.return_value = mock_result
        
        stats = TopicStatistics()
        activity = await stats.get_activity(mock_db, mock_row.topic_id, days=30)
        
        assert activity is not None
        assert activity.item_count == 10
        assert activity.decision_count == 3


class TestTopicLoader:
    """Tests for TopicLoader class."""
    
    def test_load_from_yaml(self, tmp_path):
        from analytics.topics import TopicLoader
        
        # Create test YAML file
        yaml_content = """
topics:
  - name: "Test"
    slug: "test"
    children:
      - name: "Child"
        slug: "child"
"""
        yaml_file = tmp_path / "topics.yaml"
        yaml_file.write_text(yaml_content)
        
        topics = TopicLoader.load_from_yaml(str(yaml_file))
        
        assert len(topics) == 1
        assert topics[0]["name"] == "Test"
        assert len(topics[0]["children"]) == 1


class TestTopicAssignment:
    """Tests for TopicAssignment dataclass."""
    
    def test_creation(self):
        from analytics.topics import TopicAssignment
        
        assignment = TopicAssignment(
            topic_slug="finance",
            confidence=0.85,
        )
        
        assert assignment.topic_slug == "finance"
        assert assignment.confidence == 0.85
        assert assignment.topic_id is None


# Run with: pytest tests/test_topics.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
