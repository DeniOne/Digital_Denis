"""
Digital Den — Logic Analysis Unit Tests
═══════════════════════════════════════════════════════════════════════════

Tests for logic.py and decision analysis.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

import sys
sys.path.insert(0, '.')


class TestLogicAnalyzer:
    """Tests for LogicAnalyzer class."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        return db
    
    @pytest.fixture
    def mock_groq(self):
        with patch('analytics.logic.groq') as mock:
            mock.complete_simple = AsyncMock(return_value='{"hypothesis": "Test", "arguments": [], "counterarguments": [], "assumptions": [], "confidence": 0.7}')
            yield mock


class TestExtractStructure:
    """Tests for _extract_structure method."""
    
    @pytest.fixture
    def mock_groq(self):
        with patch('analytics.logic.groq') as mock:
            yield mock
    
    @pytest.mark.asyncio
    async def test_extract_structure_parses_json(self, mock_groq):
        mock_groq.complete_simple = AsyncMock(return_value='''
        {
            "hypothesis": "Увеличить бюджет на 20%",
            "arguments": [{"content": "ROI положительный", "strength": "strong"}],
            "counterarguments": [],
            "assumptions": [{"content": "Рынок стабилен", "verified": false, "risk_if_wrong": "high"}],
            "confidence": 0.8,
            "urgency": "medium",
            "reversibility": "moderate"
        }
        ''')
        
        from analytics.logic import LogicAnalyzer
        from memory.models import MemoryItem
        
        analyzer = LogicAnalyzer()
        decision = MemoryItem(
            id=uuid4(),
            item_type="decision",
            content="Решил увеличить бюджет на 20%"
        )
        
        structure = await analyzer._extract_structure(decision)
        
        assert structure.hypothesis == "Увеличить бюджет на 20%"
        assert len(structure.arguments) == 1
        assert structure.arguments[0].strength == "strong"
        assert len(structure.assumptions) == 1
        assert structure.assumptions[0].verified == False


class TestValidateLogic:
    """Tests for _validate_logic method."""
    
    @pytest.fixture
    def mock_groq(self):
        with patch('analytics.logic.groq') as mock:
            mock.complete_simple = AsyncMock(return_value='[]')
            yield mock
    
    @pytest.mark.asyncio
    async def test_validate_detects_missing_counterarguments(self, mock_groq):
        from analytics.logic import LogicAnalyzer, DecisionStructure
        
        analyzer = LogicAnalyzer()
        structure = DecisionStructure(
            hypothesis="Test decision",
            arguments=[],
            counterarguments=[],  # None!
            assumptions=[],
        )
        
        issues = await analyzer._validate_logic(structure)
        
        # Should detect missing counterarguments
        issue_types = [i.issue_type for i in issues]
        assert "ignored_counterargument" in issue_types
    
    @pytest.mark.asyncio
    async def test_validate_detects_unverified_assumptions(self, mock_groq):
        from analytics.logic import LogicAnalyzer, DecisionStructure, Assumption
        
        analyzer = LogicAnalyzer()
        structure = DecisionStructure(
            hypothesis="Test",
            assumptions=[
                Assumption(content="High risk assumption", verified=False, risk_if_wrong="high")
            ],
        )
        
        issues = await analyzer._validate_logic(structure)
        
        issue_types = [i.issue_type for i in issues]
        assert "unverified_assumption" in issue_types


class TestAssessRisks:
    """Tests for _assess_risks method."""
    
    @pytest.mark.asyncio
    async def test_assess_risks_from_assumptions(self):
        from analytics.logic import LogicAnalyzer, DecisionStructure, Assumption
        
        analyzer = LogicAnalyzer()
        structure = DecisionStructure(
            hypothesis="Test",
            assumptions=[
                Assumption(content="Market stable", verified=False, risk_if_wrong="high")
            ],
        )
        
        risks = await analyzer._assess_risks(structure, [])
        
        assert len(risks) >= 1
        assert risks[0].risk_type == "assumption_failure"


class TestCalculateScore:
    """Tests for score calculation."""
    
    def test_score_with_arguments(self):
        from analytics.logic import LogicAnalyzer, DecisionStructure, Argument
        
        analyzer = LogicAnalyzer()
        
        structure = DecisionStructure(
            hypothesis="Test",
            arguments=[
                Argument(content="Arg 1", strength="strong"),
                Argument(content="Arg 2", strength="strong"),
            ],
            counterarguments=[
                Argument(content="Counter", strength="moderate"),
            ],
            confidence=0.8,
        )
        
        score = analyzer._calculate_score(structure, [], [])
        
        assert score > 0.5  # Should be above base
    
    def test_score_penalizes_issues(self):
        from analytics.logic import LogicAnalyzer, DecisionStructure, LogicIssue
        
        analyzer = LogicAnalyzer()
        
        structure = DecisionStructure(hypothesis="Test", confidence=0.8)
        issues = [
            LogicIssue(issue_type="test", severity="high", description="Problem")
        ]
        
        score_without = analyzer._calculate_score(structure, [], [])
        score_with = analyzer._calculate_score(structure, issues, [])
        
        assert score_with < score_without


class TestFindStrongPoints:
    """Tests for _find_strong_points method."""
    
    def test_finds_multiple_arguments(self):
        from analytics.logic import LogicAnalyzer, DecisionStructure, Argument
        
        analyzer = LogicAnalyzer()
        
        structure = DecisionStructure(
            hypothesis="A clear decision about something important",
            arguments=[
                Argument(content="Arg 1", strength="strong"),
                Argument(content="Arg 2", strength="strong"),
            ],
        )
        
        points = analyzer._find_strong_points(structure)
        
        assert any("аргумент" in p.lower() for p in points)
    
    def test_finds_evidence(self):
        from analytics.logic import LogicAnalyzer, DecisionStructure, Argument
        
        analyzer = LogicAnalyzer()
        
        structure = DecisionStructure(
            hypothesis="Test decision",
            arguments=[
                Argument(content="Arg", strength="strong", evidence="Data shows X"),
            ],
        )
        
        points = analyzer._find_strong_points(structure)
        
        assert any("доказательств" in p.lower() for p in points)


class TestRecommendation:
    """Tests for recommendation generation."""
    
    def test_high_score_low_risk(self):
        from analytics.logic import LogicAnalyzer
        
        analyzer = LogicAnalyzer()
        rec = analyzer._generate_recommendation(0.85, "low")
        
        assert "выполнению" in rec.lower()
    
    def test_low_score(self):
        from analytics.logic import LogicAnalyzer
        
        analyzer = LogicAnalyzer()
        rec = analyzer._generate_recommendation(0.3, "high")
        
        assert "доработка" in rec.lower()


class TestDataClasses:
    """Tests for data classes."""
    
    def test_decision_structure_creation(self):
        from analytics.logic import DecisionStructure
        
        structure = DecisionStructure(
            hypothesis="Test",
            confidence=0.8,
            urgency="high",
        )
        
        assert structure.hypothesis == "Test"
        assert structure.arguments == []  # Default empty list
    
    def test_logic_issue_creation(self):
        from analytics.logic import LogicIssue
        
        issue = LogicIssue(
            issue_type="circular_reasoning",
            severity="high",
            description="Argument is just a restatement",
        )
        
        assert issue.severity == "high"
    
    def test_risk_creation(self):
        from analytics.logic import Risk
        
        risk = Risk(
            risk_type="execution_risk",
            impact="high",
            likelihood="medium",
            description="May fail",
            mitigation="Plan B",
        )
        
        assert risk.mitigation == "Plan B"


class TestDecisionAnalysisService:
    """Tests for DecisionAnalysisService."""
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        from analytics.logic import DecisionAnalysisService
        
        db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_result.scalar.return_value = 0
        db.execute = AsyncMock(return_value=mock_result)
        
        service = DecisionAnalysisService()
        stats = await service.get_stats(db)
        
        assert "total_analyses" in stats
        assert "average_score" in stats


# Run with: pytest tests/test_logic.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
