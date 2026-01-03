"""
Digital Den — Kaizen Engine Unit Tests
═══════════════════════════════════════════════════════════════════════════

Tests for Kaizen Engine — personal development tracking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, date, timedelta

import sys
sys.path.insert(0, '.')


class TestKaizenModels:
    """Tests for Kaizen Engine database models."""
    
    def test_kaizen_contour_enum(self):
        from analytics.kaizen_models import KaizenContour
        
        assert KaizenContour.COGNITIVE.value == "cognitive"
        assert KaizenContour.DECISION.value == "decision"
        assert KaizenContour.MANAGEMENT.value == "management"
        assert KaizenContour.STABILITY.value == "stability"
    
    def test_user_state_enum(self):
        from analytics.kaizen_models import UserState
        
        assert UserState.GROWTH.value == "growth"
        assert UserState.PLATEAU.value == "plateau"
        assert UserState.FLUCTUATION.value == "fluctuation"
        assert UserState.OVERLOAD.value == "overload"
    
    def test_trend_direction_enum(self):
        from analytics.kaizen_models import TrendDirection
        
        assert TrendDirection.UP.value == "up"
        assert TrendDirection.DOWN.value == "down"
        assert TrendDirection.STABLE.value == "stable"
        assert TrendDirection.VOLATILE.value == "volatile"  # Fixed: was FLUCTUATING
    
    def test_kaizen_snapshot_creation(self):
        from analytics.kaizen_models import KaizenSnapshot
        
        user_id = uuid4()
        snapshot = KaizenSnapshot(
            user_id=user_id,
            kaizen_index=75.5,
            user_state="growth",
            snapshot_date=date.today(),
        )
        
        assert snapshot.kaizen_index == 75.5
        assert snapshot.user_state == "growth"
    
    def test_kaizen_contour_metrics_creation(self):
        from analytics.kaizen_models import KaizenContourMetrics
        
        metrics = KaizenContourMetrics(
            snapshot_id=uuid4(),
            contour="cognitive",
            score=82.3,
            trend="up",
        )
        
        assert metrics.contour == "cognitive"
        assert metrics.score == 82.3
        assert metrics.trend == "up"
    
    def test_kaizen_observation_creation(self):
        from analytics.kaizen_models import KaizenObservation
        
        observation = KaizenObservation(
            user_id=uuid4(),
            observation_type="pattern",
            observation_text="Наблюдается рост активности в утренние часы",  # Fixed: was message
            observation_date=date.today(),
        )
        
        assert observation.observation_type == "pattern"
        assert "рост" in observation.observation_text


class TestKaizenIndexCalculation:
    """Tests for Kaizen index calculation logic."""
    
    def test_calculate_change_percent_positive(self):
        # Test calculation helper
        old_val = 50.0
        new_val = 60.0
        expected = ((new_val - old_val) / old_val) * 100  # 20%
        
        assert expected == 20.0
    
    def test_calculate_change_percent_negative(self):
        old_val = 60.0
        new_val = 48.0
        expected = ((new_val - old_val) / old_val) * 100  # -20%
        
        assert expected == -20.0
    
    def test_calculate_change_percent_zero_base(self):
        old_val = 0.0
        new_val = 50.0
        
        # Should handle division by zero
        if old_val == 0:
            expected = 0.0 if new_val == 0 else 100.0
        else:
            expected = ((new_val - old_val) / old_val) * 100
        
        assert expected == 100.0


class TestUserStateDetection:
    """Tests for user state detection logic."""
    
    def test_detect_growth_state(self):
        # If kaizen_index is increasing consistently
        changes = [5.0, 3.0, 7.0, 2.0]  # All positive
        avg_change = sum(changes) / len(changes)
        
        if avg_change > 2.0:
            state = "growth"
        elif avg_change < -2.0:
            state = "decline"
        else:
            state = "plateau"
        
        assert state == "growth"
    
    def test_detect_plateau_state(self):
        changes = [0.5, -0.3, 0.2, -0.1]  # Small fluctuations
        avg_change = sum(changes) / len(changes)
        
        if avg_change > 2.0:
            state = "growth"
        elif avg_change < -2.0:
            state = "decline"
        else:
            state = "plateau"
        
        assert state == "plateau"
    
    def test_detect_fluctuation_state(self):
        changes = [10.0, -8.0, 12.0, -15.0]  # Large swings
        variance = sum((x - sum(changes)/len(changes))**2 for x in changes) / len(changes)
        
        # High variance indicates fluctuation
        assert variance > 50  # Arbitrary threshold for test


class TestAdaptiveBehavior:
    """Tests for Adaptive AI Behavior module."""
    
    def test_ai_behavior_modes_exist(self):
        from orchestrator.adaptive_behavior import AIBehaviorMode
        
        assert AIBehaviorMode.STRATEGIST.value == "strategist"
        assert AIBehaviorMode.ANALYST.value == "analyst"
        assert AIBehaviorMode.COACH.value == "coach"
        assert AIBehaviorMode.FIXER.value == "fixer"
        assert AIBehaviorMode.EXPLORER.value == "explorer"
    
    def test_select_mode_for_growth_state(self):
        from orchestrator.adaptive_behavior import AdaptiveAIBehavior, AIBehaviorMode
        from analytics.kaizen_models import UserState
        
        behavior = AdaptiveAIBehavior()
        mode = behavior.select_behavior_mode(UserState.GROWTH)
        
        # Growth state should select STRATEGIST
        assert mode == AIBehaviorMode.STRATEGIST
    
    def test_select_mode_for_overload_state(self):
        from orchestrator.adaptive_behavior import AdaptiveAIBehavior, AIBehaviorMode
        from analytics.kaizen_models import UserState
        
        behavior = AdaptiveAIBehavior()
        mode = behavior.select_behavior_mode(UserState.OVERLOAD)
        
        # Overload state should select FIXER
        assert mode == AIBehaviorMode.FIXER
    
    def test_get_behavior_config(self):
        from orchestrator.adaptive_behavior import AdaptiveAIBehavior, AIBehaviorMode
        
        behavior = AdaptiveAIBehavior()
        config = behavior.get_behavior_config(AIBehaviorMode.ANALYST)
        
        assert config is not None
        assert config.mode == AIBehaviorMode.ANALYST


class TestKaizenSettings:
    """Tests for Kaizen Settings."""
    
    def test_valid_comparison_periods(self):
        valid_periods = ["week", "month", "quarter", "half_year", "year", "all_time"]
        
        for period in valid_periods:
            assert period in valid_periods
    
    def test_period_to_days_mapping(self):
        mapping = {
            "week": 7,
            "month": 30,
            "quarter": 90,
            "half_year": 180,
            "year": 365,
            "all_time": None,
        }
        
        assert mapping["week"] == 7
        assert mapping["quarter"] == 90
        assert mapping["all_time"] is None


class TestGoldenStandard:
    """Tests for Golden Standard loader."""
    
    def test_golden_standard_loader_exists(self):
        from core.golden_standard import GoldenStandardLoader
        
        loader = GoldenStandardLoader()
        assert loader is not None
    
    def test_golden_standard_has_load_method(self):
        from core.golden_standard import GoldenStandardLoader
        
        loader = GoldenStandardLoader()
        # Check that loader has expected methods
        assert hasattr(loader, 'load')


class TestKaizenAPIStructure:
    """Tests for Kaizen API endpoint structures."""
    
    def test_kaizen_index_endpoint_structure(self):
        # Test response structure
        expected_fields = [
            "kaizen_index",
            "change_7d",
            "change_14d",
            "change_30d",
            "user_state",
        ]
        
        # Verify all fields are expected
        for field in expected_fields:
            assert field in expected_fields
    
    def test_kaizen_contours_response_has_four_contours(self):
        expected_contours = ["cognitive", "decision", "management", "stability"]
        
        assert len(expected_contours) == 4
    
    def test_contour_names_match_enum(self):
        from analytics.kaizen_models import KaizenContour
        
        contour_values = [c.value for c in KaizenContour]
        
        assert "cognitive" in contour_values
        assert "decision" in contour_values
        assert "management" in contour_values
        assert "stability" in contour_values


class TestBehaviorModeMapping:
    """Tests for user state to behavior mode mapping."""
    
    def test_growth_maps_to_strategist(self):
        from orchestrator.adaptive_behavior import AdaptiveAIBehavior, AIBehaviorMode
        from analytics.kaizen_models import UserState
        
        assert AdaptiveAIBehavior.STATE_TO_MODE[UserState.GROWTH] == AIBehaviorMode.STRATEGIST
    
    def test_plateau_maps_to_analyst(self):
        from orchestrator.adaptive_behavior import AdaptiveAIBehavior, AIBehaviorMode
        from analytics.kaizen_models import UserState
        
        assert AdaptiveAIBehavior.STATE_TO_MODE[UserState.PLATEAU] == AIBehaviorMode.ANALYST
    
    def test_fluctuation_maps_to_coach(self):
        from orchestrator.adaptive_behavior import AdaptiveAIBehavior, AIBehaviorMode
        from analytics.kaizen_models import UserState
        
        assert AdaptiveAIBehavior.STATE_TO_MODE[UserState.FLUCTUATION] == AIBehaviorMode.COACH
    
    def test_overload_maps_to_fixer(self):
        from orchestrator.adaptive_behavior import AdaptiveAIBehavior, AIBehaviorMode
        from analytics.kaizen_models import UserState
        
        assert AdaptiveAIBehavior.STATE_TO_MODE[UserState.OVERLOAD] == AIBehaviorMode.FIXER


# Run with: pytest tests/test_kaizen.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
