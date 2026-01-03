"""
Digital Den — Kaizen Engine Service
═══════════════════════════════════════════════════════════════════════════

Core service for tracking personal development dynamics.

Principle:
> User grows, AI observes, System remembers, User sees dynamics (not verdict)

Based on: docs/kaizen_engine.md
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.kaizen_models import (
    KaizenSnapshot, KaizenContourMetrics, KaizenStateTransition,
    KaizenObservation, KaizenContour, UserState, TrendDirection
)
from memory.models import MemoryItem


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

# Thresholds for trend detection
TREND_UP_THRESHOLD = 0.05      # +5% считается ростом
TREND_DOWN_THRESHOLD = -0.05   # -5% считается снижением
VOLATILITY_THRESHOLD = 0.15    # >15% колебания = флуктуации

# State detection thresholds
OVERLOAD_ACTIVITY_THRESHOLD = 1.5   # 150% от среднего
OVERLOAD_CLARITY_DROP = -0.10       # -10% ясности

# Neutral language templates for observations
OBSERVATION_TEMPLATES = {
    "growth": [
        "Наблюдается положительная динамика по контуру «{contour}»: {detail}",
        "Зафиксирован рост {metric} на {percent}% за {period}",
    ],
    "plateau": [
        "Стабильный период по контуру «{contour}»: показатели без существенных изменений",
        "Наблюдается плато: {detail}",
    ],
    "fluctuation": [
        "Зафиксированы колебания в контуре «{contour}»: {detail}",
        "Наблюдается нестабильность: {detail}",
    ],
    "overload": [
        "Высокая активность сочетается со снижением ясности формулировок",
        "Зафиксированы признаки когнитивной перегрузки: {detail}",
    ],
}

# Contour names in Russian
CONTOUR_NAMES = {
    KaizenContour.COGNITIVE: "Когнитивный",
    KaizenContour.DECISION: "Решенческий",
    KaizenContour.MANAGEMENT: "Системность",
    KaizenContour.STABILITY: "Устойчивость",
}


# ═══════════════════════════════════════════════════════════════════════════
# Kaizen Engine Service
# ═══════════════════════════════════════════════════════════════════════════

class KaizenEngine:
    """
    Kaizen Engine — digital personal development tracking module.
    
    Core principles:
    - Only relative dynamics (T vs T-1)
    - Never compares with norms or other people
    - Uses observation language, not evaluation
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ─────────────────────────────────────────────────────────────────────────
    # Main API
    # ─────────────────────────────────────────────────────────────────────────
    
    async def get_current_kaizen_index(
        self, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get current Kaizen index and state for user.
        
        Returns:
            {
                "kaizen_index": float,  # Relative change
                "change_7d": float,
                "change_14d": float,
                "user_state": str,
                "state_label": str,
            }
        """
        snapshot = await self._get_latest_snapshot(user_id)
        
        if not snapshot:
            return {
                "kaizen_index": 0.0,
                "change_7d": 0.0,
                "change_14d": 0.0,
                "change_30d": 0.0,
                "user_state": UserState.PLATEAU.value,
                "state_label": "Начало отслеживания",
            }
        
        state_labels = {
            UserState.GROWTH.value: "Рост",
            UserState.PLATEAU.value: "Стабилизация",
            UserState.FLUCTUATION.value: "Флуктуации",
            UserState.OVERLOAD.value: "Перегруз",
        }
        
        return {
            "kaizen_index": snapshot.kaizen_index,
            "change_7d": snapshot.kaizen_index_7d,
            "change_14d": snapshot.kaizen_index_14d,
            "change_30d": snapshot.kaizen_index_30d,
            "user_state": snapshot.user_state,
            "state_label": state_labels.get(snapshot.user_state, "Неизвестно"),
        }
    
    async def get_contours(
        self, 
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all 4 Kaizen contours with current state.
        
        Returns list of:
            {
                "contour": str,
                "name": str,
                "score": float,
                "trend": str,
                "change_pct": float,
                "icon": str,
            }
        """
        snapshot = await self._get_latest_snapshot(user_id)
        
        if not snapshot:
            # Return default contours
            return self._get_default_contours()
        
        contours = [
            {
                "contour": KaizenContour.COGNITIVE.value,
                "name": "Когнитивный",
                "description": "Ясность мышления",
                "score": snapshot.cognitive_score,
                "trend": snapshot.cognitive_trend,
                "change_pct": snapshot.cognitive_change_pct,
                "icon": "🧠",
            },
            {
                "contour": KaizenContour.DECISION.value,
                "name": "Решенческий",
                "description": "Качество решений",
                "score": snapshot.decision_score,
                "trend": snapshot.decision_trend,
                "change_pct": snapshot.decision_change_pct,
                "icon": "🎯",
            },
            {
                "contour": KaizenContour.MANAGEMENT.value,
                "name": "Системность",
                "description": "Структурность мышления",
                "score": snapshot.management_score,
                "trend": snapshot.management_trend,
                "change_pct": snapshot.management_change_pct,
                "icon": "🏗",
            },
            {
                "contour": KaizenContour.STABILITY.value,
                "name": "Устойчивость",
                "description": "Психокогнитивная стабильность",
                "score": snapshot.stability_score,
                "trend": snapshot.stability_trend,
                "change_pct": snapshot.stability_change_pct,
                "icon": "🧘",
            },
        ]
        
        return contours
    
    async def get_kaizen_mirror(
        self, 
        user_id: UUID,
        limit: int = 3
    ) -> List[str]:
        """
        Get recent Kaizen Mirror observations.
        
        Mirror observations are:
        - 1-2 sentences each
        - Neutral language
        - No imperatives
        - Pure reflection
        """
        query = (
            select(KaizenObservation)
            .where(
                and_(
                    KaizenObservation.user_id == user_id,
                    KaizenObservation.is_mirror_worthy == True,
                )
            )
            .order_by(desc(KaizenObservation.created_at))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        observations = result.scalars().all()
        
        if not observations:
            # Return default observation
            return ["Система начала отслеживание. Наблюдения появятся по мере накопления данных."]
        
        return [obs.observation_text for obs in observations]
    
    async def get_history(
        self, 
        user_id: UUID,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get Kaizen index history for trend visualization.
        """
        since_date = date.today() - timedelta(days=days)
        
        query = (
            select(KaizenSnapshot)
            .where(
                and_(
                    KaizenSnapshot.user_id == user_id,
                    KaizenSnapshot.snapshot_date >= since_date,
                )
            )
            .order_by(KaizenSnapshot.snapshot_date)
        )
        
        result = await self.session.execute(query)
        snapshots = result.scalars().all()
        
        return [
            {
                "date": s.snapshot_date.isoformat(),
                "kaizen_index": s.kaizen_index,
                "user_state": s.user_state,
                "cognitive": s.cognitive_score,
                "decision": s.decision_score,
                "management": s.management_score,
                "stability": s.stability_score,
            }
            for s in snapshots
        ]
    
    # ─────────────────────────────────────────────────────────────────────────
    # Snapshot Creation (called by background worker)
    # ─────────────────────────────────────────────────────────────────────────
    
    async def create_daily_snapshot(
        self, 
        user_id: UUID,
        target_date: Optional[date] = None
    ) -> KaizenSnapshot:
        """
        Create daily Kaizen snapshot by analyzing user's data.
        
        This is the core calculation that:
        1. Gathers raw metrics from memories, messages, decisions
        2. Calculates contour scores
        3. Determines trends by comparing with previous snapshot
        4. Detects user state
        5. Generates mirror observation
        """
        target_date = target_date or date.today()
        
        # Get previous snapshot for comparison
        prev_snapshot = await self._get_previous_snapshot(user_id, target_date)
        
        # Calculate raw metrics for today
        raw_metrics = await self._calculate_raw_metrics(user_id, target_date)
        
        # Calculate contour scores
        contour_scores = self._calculate_contour_scores(raw_metrics, prev_snapshot)
        
        # Detect trends
        trends = self._detect_trends(contour_scores, prev_snapshot)
        
        # Detect user state
        user_state = self._detect_user_state(contour_scores, trends, raw_metrics)
        
        # Calculate Kaizen index
        kaizen_index = self._calculate_kaizen_index(contour_scores, prev_snapshot)
        
        # Calculate period changes
        kaizen_7d = await self._calculate_period_change(user_id, target_date, 7)
        kaizen_14d = await self._calculate_period_change(user_id, target_date, 14)
        kaizen_30d = await self._calculate_period_change(user_id, target_date, 30)
        
        # Generate mirror observation
        mirror_obs = self._generate_mirror_observation(
            contour_scores, trends, user_state, raw_metrics
        )
        
        # Create snapshot
        snapshot = KaizenSnapshot(
            user_id=user_id,
            snapshot_date=target_date,
            kaizen_index=kaizen_index,
            kaizen_index_7d=kaizen_7d,
            kaizen_index_14d=kaizen_14d,
            kaizen_index_30d=kaizen_30d,
            user_state=user_state.value,
            cognitive_score=contour_scores["cognitive"]["score"],
            cognitive_trend=trends["cognitive"].value,
            cognitive_change_pct=contour_scores["cognitive"]["change_pct"],
            decision_score=contour_scores["decision"]["score"],
            decision_trend=trends["decision"].value,
            decision_change_pct=contour_scores["decision"]["change_pct"],
            management_score=contour_scores["management"]["score"],
            management_trend=trends["management"].value,
            management_change_pct=contour_scores["management"]["change_pct"],
            stability_score=contour_scores["stability"]["score"],
            stability_trend=trends["stability"].value,
            stability_change_pct=contour_scores["stability"]["change_pct"],
            avg_message_length=raw_metrics.get("avg_message_length", 0),
            formulation_precision=raw_metrics.get("formulation_precision", 0),
            abstraction_level=raw_metrics.get("abstraction_level", 0),
            topic_switches=raw_metrics.get("topic_switches", 0),
            decision_completion_rate=raw_metrics.get("decision_completion_rate", 0),
            revisit_rate=raw_metrics.get("revisit_rate", 0),
            messages_count=raw_metrics.get("messages_count", 0),
            decisions_count=raw_metrics.get("decisions_count", 0),
            insights_count=raw_metrics.get("insights_count", 0),
            mirror_observation=mirror_obs,
        )
        
        self.session.add(snapshot)
        
        # Check for state transition
        if prev_snapshot and prev_snapshot.user_state != user_state.value:
            await self._record_state_transition(
                user_id, prev_snapshot.user_state, user_state.value, target_date
            )
        
        # Create mirror-worthy observation if significant
        if mirror_obs:
            await self._create_observation(
                user_id, target_date, mirror_obs, snapshot.id, is_mirror=True
            )
        
        await self.session.commit()
        
        return snapshot
    
    # ─────────────────────────────────────────────────────────────────────────
    # State Detection for AI Behavior
    # ─────────────────────────────────────────────────────────────────────────
    
    async def get_user_state_for_ai(
        self, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get user state information for Adaptive AI Behavior module.
        
        Returns enriched state data that AI uses to adapt its behavior.
        """
        snapshot = await self._get_latest_snapshot(user_id)
        
        if not snapshot:
            return {
                "state": UserState.PLATEAU.value,
                "confidence": 0.5,
                "contours": self._get_default_contours(),
                "recommendations": {
                    "behavior_mode": "strategist",
                    "thinking_depth": "structured",
                    "response_length": "medium",
                },
            }
        
        # Determine AI recommendations based on state
        recommendations = self._get_ai_recommendations(snapshot)
        
        return {
            "state": snapshot.user_state,
            "confidence": 0.8,  # Based on data availability
            "kaizen_index": snapshot.kaizen_index,
            "contours": {
                "cognitive": {"score": snapshot.cognitive_score, "trend": snapshot.cognitive_trend},
                "decision": {"score": snapshot.decision_score, "trend": snapshot.decision_trend},
                "management": {"score": snapshot.management_score, "trend": snapshot.management_trend},
                "stability": {"score": snapshot.stability_score, "trend": snapshot.stability_trend},
            },
            "recommendations": recommendations,
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # Private Methods
    # ─────────────────────────────────────────────────────────────────────────
    
    async def _get_latest_snapshot(self, user_id: UUID) -> Optional[KaizenSnapshot]:
        """Get most recent snapshot for user."""
        query = (
            select(KaizenSnapshot)
            .where(KaizenSnapshot.user_id == user_id)
            .order_by(desc(KaizenSnapshot.snapshot_date))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_previous_snapshot(
        self, user_id: UUID, before_date: date
    ) -> Optional[KaizenSnapshot]:
        """Get snapshot before specified date."""
        query = (
            select(KaizenSnapshot)
            .where(
                and_(
                    KaizenSnapshot.user_id == user_id,
                    KaizenSnapshot.snapshot_date < before_date,
                )
            )
            .order_by(desc(KaizenSnapshot.snapshot_date))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _calculate_raw_metrics(
        self, user_id: UUID, target_date: date
    ) -> Dict[str, Any]:
        """Calculate raw metrics from user's data for the day."""
        # For now, return placeholder metrics
        # TODO: Integrate with real data from messages, memories, decisions
        
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date, datetime.max.time())
        
        # Count memories by type
        memory_query = (
            select(
                MemoryItem.memory_type,
                func.count(MemoryItem.id).label("count"),
            )
            .where(
                and_(
                    MemoryItem.user_id == user_id,
                    MemoryItem.created_at >= start_dt,
                    MemoryItem.created_at <= end_dt,
                )
            )
            .group_by(MemoryItem.memory_type)
        )
        
        result = await self.session.execute(memory_query)
        type_counts = {row[0]: row[1] for row in result.fetchall()}
        
        return {
            "messages_count": type_counts.get("context", 0),
            "decisions_count": type_counts.get("decision", 0),
            "insights_count": type_counts.get("insight", 0),
            "avg_message_length": 0.0,  # TODO: Calculate from actual messages
            "formulation_precision": 0.5,  # TODO: Analyze with LLM
            "abstraction_level": 0.5,  # TODO: Analyze with LLM
            "topic_switches": 0,  # TODO: Detect from topic changes
            "decision_completion_rate": 0.5,  # TODO: Track decisions
            "revisit_rate": 0.0,  # TODO: Track topic revisits
        }
    
    def _calculate_contour_scores(
        self, 
        raw_metrics: Dict[str, Any],
        prev_snapshot: Optional[KaizenSnapshot]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate scores for each contour."""
        # Start with previous scores or defaults
        prev_cognitive = prev_snapshot.cognitive_score if prev_snapshot else 0.5
        prev_decision = prev_snapshot.decision_score if prev_snapshot else 0.5
        prev_management = prev_snapshot.management_score if prev_snapshot else 0.5
        prev_stability = prev_snapshot.stability_score if prev_snapshot else 0.5
        
        # Calculate new scores based on metrics
        # Cognitive: based on formulation precision and abstraction
        cognitive = (
            raw_metrics.get("formulation_precision", 0.5) * 0.6 +
            raw_metrics.get("abstraction_level", 0.5) * 0.4
        )
        
        # Decision: based on decision count and completion rate
        decisions = raw_metrics.get("decisions_count", 0)
        completion = raw_metrics.get("decision_completion_rate", 0.5)
        decision = min(1.0, decisions / 5) * 0.4 + completion * 0.6 if decisions > 0 else prev_decision
        
        # Management: based on topic switches (less is better) and structure
        topic_switches = raw_metrics.get("topic_switches", 0)
        management = max(0.3, 1.0 - topic_switches * 0.1) if topic_switches else prev_management
        
        # Stability: based on activity consistency
        messages = raw_metrics.get("messages_count", 0)
        prev_messages = prev_snapshot.messages_count if prev_snapshot else messages
        activity_change = abs(messages - prev_messages) / max(prev_messages, 1)
        stability = max(0.3, 1.0 - activity_change * 0.5) if prev_snapshot else 0.5
        
        return {
            "cognitive": {
                "score": round(cognitive, 3),
                "change_pct": round((cognitive - prev_cognitive) / max(prev_cognitive, 0.01) * 100, 1),
            },
            "decision": {
                "score": round(decision, 3),
                "change_pct": round((decision - prev_decision) / max(prev_decision, 0.01) * 100, 1),
            },
            "management": {
                "score": round(management, 3),
                "change_pct": round((management - prev_management) / max(prev_management, 0.01) * 100, 1),
            },
            "stability": {
                "score": round(stability, 3),
                "change_pct": round((stability - prev_stability) / max(prev_stability, 0.01) * 100, 1),
            },
        }
    
    def _detect_trends(
        self,
        contour_scores: Dict[str, Dict[str, float]],
        prev_snapshot: Optional[KaizenSnapshot]
    ) -> Dict[str, TrendDirection]:
        """Detect trend direction for each contour."""
        trends = {}
        
        for contour, data in contour_scores.items():
            change = data["change_pct"] / 100  # Convert back to decimal
            
            if abs(change) > VOLATILITY_THRESHOLD:
                trends[contour] = TrendDirection.VOLATILE
            elif change >= TREND_UP_THRESHOLD:
                trends[contour] = TrendDirection.UP
            elif change <= TREND_DOWN_THRESHOLD:
                trends[contour] = TrendDirection.DOWN
            else:
                trends[contour] = TrendDirection.STABLE
        
        return trends
    
    def _detect_user_state(
        self,
        contour_scores: Dict[str, Dict[str, float]],
        trends: Dict[str, TrendDirection],
        raw_metrics: Dict[str, Any]
    ) -> UserState:
        """Detect overall user cognitive state."""
        # Count trends
        up_count = sum(1 for t in trends.values() if t == TrendDirection.UP)
        down_count = sum(1 for t in trends.values() if t == TrendDirection.DOWN)
        volatile_count = sum(1 for t in trends.values() if t == TrendDirection.VOLATILE)
        
        # Check for overload
        stability_score = contour_scores["stability"]["score"]
        cognitive_score = contour_scores["cognitive"]["score"]
        if stability_score < 0.4 and cognitive_score < 0.4:
            return UserState.OVERLOAD
        
        # Check for fluctuations
        if volatile_count >= 2:
            return UserState.FLUCTUATION
        
        # Check for growth
        if up_count >= 2 and down_count == 0:
            return UserState.GROWTH
        
        # Default to plateau
        return UserState.PLATEAU
    
    def _calculate_kaizen_index(
        self,
        contour_scores: Dict[str, Dict[str, float]],
        prev_snapshot: Optional[KaizenSnapshot]
    ) -> float:
        """Calculate aggregated Kaizen index."""
        # Weighted average of contour changes
        weights = {
            "cognitive": 0.3,
            "decision": 0.25,
            "management": 0.25,
            "stability": 0.2,
        }
        
        total_change = sum(
            contour_scores[c]["change_pct"] * w
            for c, w in weights.items()
        )
        
        return round(total_change, 2)
    
    async def _calculate_period_change(
        self, user_id: UUID, target_date: date, days: int
    ) -> float:
        """Calculate change over specified period."""
        past_date = target_date - timedelta(days=days)
        
        query = (
            select(KaizenSnapshot)
            .where(
                and_(
                    KaizenSnapshot.user_id == user_id,
                    KaizenSnapshot.snapshot_date >= past_date,
                    KaizenSnapshot.snapshot_date <= target_date,
                )
            )
            .order_by(KaizenSnapshot.snapshot_date)
        )
        
        result = await self.session.execute(query)
        snapshots = result.scalars().all()
        
        if len(snapshots) < 2:
            return 0.0
        
        first = snapshots[0]
        last = snapshots[-1]
        
        # Calculate aggregate change
        cognitive_change = last.cognitive_score - first.cognitive_score
        decision_change = last.decision_score - first.decision_score
        management_change = last.management_score - first.management_score
        stability_change = last.stability_score - first.stability_score
        
        avg_change = (cognitive_change + decision_change + management_change + stability_change) / 4
        return round(avg_change * 100, 2)  # Convert to percentage
    
    def _generate_mirror_observation(
        self,
        contour_scores: Dict[str, Dict[str, float]],
        trends: Dict[str, TrendDirection],
        user_state: UserState,
        raw_metrics: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate Kaizen Mirror observation.
        
        Rules:
        - No imperatives
        - No recommendations
        - Pure reflection
        """
        # Find most significant change
        max_change = 0
        max_contour = None
        for contour, data in contour_scores.items():
            if abs(data["change_pct"]) > abs(max_change):
                max_change = data["change_pct"]
                max_contour = contour
        
        if abs(max_change) < 2:  # Less than 2% change - not significant
            return None
        
        contour_name = CONTOUR_NAMES.get(
            KaizenContour(max_contour), max_contour
        )
        
        if max_change > 0:
            return f"Наблюдается улучшение показателей по контуру «{contour_name}» (+{max_change:.1f}%)"
        else:
            return f"Зафиксировано снижение в контуре «{contour_name}» ({max_change:.1f}%)"
    
    async def _record_state_transition(
        self,
        user_id: UUID,
        from_state: str,
        to_state: str,
        transition_date: date
    ):
        """Record state transition for history."""
        transition = KaizenStateTransition(
            user_id=user_id,
            from_state=from_state,
            to_state=to_state,
            transition_date=transition_date,
        )
        self.session.add(transition)
    
    async def _create_observation(
        self,
        user_id: UUID,
        obs_date: date,
        text: str,
        snapshot_id: Optional[UUID],
        is_mirror: bool = False
    ):
        """Create Kaizen observation."""
        observation = KaizenObservation(
            user_id=user_id,
            observation_date=obs_date,
            observation_text=text,
            snapshot_id=snapshot_id,
            is_mirror_worthy=is_mirror,
        )
        self.session.add(observation)
    
    def _get_default_contours(self) -> List[Dict[str, Any]]:
        """Return default contour values."""
        return [
            {
                "contour": "cognitive",
                "name": "Когнитивный",
                "description": "Ясность мышления",
                "score": 0.5,
                "trend": TrendDirection.STABLE.value,
                "change_pct": 0.0,
                "icon": "🧠",
            },
            {
                "contour": "decision",
                "name": "Решенческий",
                "description": "Качество решений",
                "score": 0.5,
                "trend": TrendDirection.STABLE.value,
                "change_pct": 0.0,
                "icon": "🎯",
            },
            {
                "contour": "management",
                "name": "Системность",
                "description": "Структурность мышления",
                "score": 0.5,
                "trend": TrendDirection.STABLE.value,
                "change_pct": 0.0,
                "icon": "🏗",
            },
            {
                "contour": "stability",
                "name": "Устойчивость",
                "description": "Психокогнитивная стабильность",
                "score": 0.5,
                "trend": TrendDirection.STABLE.value,
                "change_pct": 0.0,
                "icon": "🧘",
            },
        ]
    
    def _get_ai_recommendations(
        self, snapshot: KaizenSnapshot
    ) -> Dict[str, str]:
        """
        Get AI behavior recommendations based on user state.
        
        Based on: docs/adaptive_ai_behavior.md
        """
        state = UserState(snapshot.user_state)
        
        recommendations = {
            UserState.GROWTH: {
                "behavior_mode": "strategist",  # Партнёр-стратег
                "thinking_depth": "deep",
                "response_length": "detailed",
                "focus": "расширение горизонтов, модели, архитектура",
            },
            UserState.PLATEAU: {
                "behavior_mode": "analyst",  # Логический аналитик
                "thinking_depth": "structured",
                "response_length": "medium",
                "focus": "уточняющие вопросы, альтернативные углы",
            },
            UserState.FLUCTUATION: {
                "behavior_mode": "coach",  # Коуч (сократический)
                "thinking_depth": "structured",
                "response_length": "medium",
                "focus": "вопросы важнее ответов, прояснение намерений",
            },
            UserState.OVERLOAD: {
                "behavior_mode": "fixer",  # Фиксатор
                "thinking_depth": "shallow",
                "response_length": "brief",
                "focus": "кратко, чётко, зафиксировать и остановиться",
            },
        }
        
        return recommendations.get(state, recommendations[UserState.PLATEAU])
