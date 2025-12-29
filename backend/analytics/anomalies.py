"""
Digital Denis — Anomaly Detection Engine
═══════════════════════════════════════════════════════════════════════════

Advanced anomaly detection for thinking patterns.
"""

import json
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.cal_models import CALAnomaly, CALTopicStats, CALDecisionAnalysis
from memory.models import MemoryItem, Topic
from llm.groq import groq


# ═══════════════════════════════════════════════════════════════════════════
# Enums and Constants
# ═══════════════════════════════════════════════════════════════════════════

class AnomalyType(str, Enum):
    TOPIC_SPIKE = "topic_spike"
    TOPIC_DISAPPEARANCE = "topic_disappearance"
    DECISION_SURGE = "decision_surge"
    DECISION_DROUGHT = "decision_drought"
    CONFIDENCE_SPIKE = "confidence_spike"
    CONFIDENCE_DROP = "confidence_drop"
    QUALITY_DEGRADATION = "quality_degradation"
    TOPIC_NARROWING = "topic_narrowing"
    HIGH_RISK_DECISION = "high_risk_decision"
    CONTRADICTION_DETECTED = "contradiction_detected"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Thresholds for anomaly detection
THRESHOLDS = {
    "topic_spike": 0.5,           # +50%
    "topic_drop": 0.7,            # -70%
    "decision_surge": 2.0,        # x2
    "decision_drought": 0.3,      # -70%
    "confidence_shift": 0.3,      # ±30%
    "quality_drop": 0.2,          # -20%
    "min_topic_diversity": 3,     # minimum active topics
}

# Severity mapping by anomaly type
SEVERITY_MAP = {
    AnomalyType.TOPIC_SPIKE: Severity.MEDIUM,
    AnomalyType.TOPIC_DISAPPEARANCE: Severity.MEDIUM,
    AnomalyType.DECISION_SURGE: Severity.HIGH,
    AnomalyType.DECISION_DROUGHT: Severity.MEDIUM,
    AnomalyType.CONFIDENCE_SPIKE: Severity.MEDIUM,
    AnomalyType.CONFIDENCE_DROP: Severity.HIGH,
    AnomalyType.QUALITY_DEGRADATION: Severity.CRITICAL,
    AnomalyType.TOPIC_NARROWING: Severity.MEDIUM,
    AnomalyType.HIGH_RISK_DECISION: Severity.HIGH,
    AnomalyType.CONTRADICTION_DETECTED: Severity.MEDIUM,
}


# ═══════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Baseline:
    """Baseline metrics for comparison."""
    period_days: int
    topic_frequencies: Dict[UUID, float] = field(default_factory=dict)
    topic_names: Dict[UUID, str] = field(default_factory=dict)
    decision_count: int = 0
    avg_confidence: float = 0.0
    avg_quality: float = 0.0
    active_topics: int = 0
    total_items: int = 0


@dataclass
class CurrentMetrics:
    """Current period metrics."""
    period_days: int
    topic_frequencies: Dict[UUID, float] = field(default_factory=dict)
    decision_count: int = 0
    avg_confidence: float = 0.0
    avg_quality: float = 0.0
    active_topics: int = 0
    total_items: int = 0


@dataclass
class Anomaly:
    """Detected anomaly."""
    anomaly_type: AnomalyType
    severity: Severity
    title: str
    description: str
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    deviation_percent: Optional[float] = None
    topic_id: Optional[UUID] = None
    topic_name: Optional[str] = None
    memory_id: Optional[UUID] = None
    interpretation: Optional[str] = None
    suggested_action: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# Anomaly Detector
# ═══════════════════════════════════════════════════════════════════════════

class AnomalyDetector:
    """
    Anomaly detection engine for thinking patterns.
    
    Compares current metrics against baseline to detect:
    - Topic spikes/disappearances
    - Decision rate anomalies
    - Confidence shifts
    - Quality degradation
    - Topic diversity issues
    """
    
    def __init__(self):
        self.thresholds = THRESHOLDS.copy()
    
    async def detect(
        self,
        db: AsyncSession,
        baseline_days: int = 30,
        current_days: int = 7,
    ) -> List[Anomaly]:
        """
        Run full anomaly detection.
        
        Args:
            baseline_days: Period for baseline calculation (default 30)
            current_days: Period for current metrics (default 7)
        """
        anomalies = []
        
        # Get baseline and current metrics
        baseline = await self._get_baseline(db, baseline_days)
        current = await self._get_current(db, current_days)
        
        # Topic anomalies
        topic_anomalies = self._check_topics(baseline, current)
        anomalies.extend(topic_anomalies)
        
        # Decision rate anomalies
        decision_anomalies = self._check_decisions(baseline, current)
        anomalies.extend(decision_anomalies)
        
        # Confidence anomalies
        confidence_anomalies = self._check_confidence(baseline, current)
        anomalies.extend(confidence_anomalies)
        
        # Quality anomalies
        quality_anomalies = await self._check_quality(db, baseline, current)
        anomalies.extend(quality_anomalies)
        
        # Topic diversity anomalies
        diversity_anomalies = self._check_topic_diversity(current)
        anomalies.extend(diversity_anomalies)
        
        # Generate interpretations for all anomalies
        for anomaly in anomalies:
            if not anomaly.interpretation:
                anomaly.interpretation = await self._interpret(anomaly)
        
        return anomalies
    
    async def _get_baseline(
        self,
        db: AsyncSession,
        days: int
    ) -> Baseline:
        """Calculate baseline metrics for comparison."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get topic frequencies
        topic_freq = {}
        topic_names = {}
        
        result = await db.execute(
            select(
                CALTopicStats.topic_id,
                func.sum(CALTopicStats.item_count).label("total"),
                Topic.name.label("topic_name")
            )
            .join(Topic, Topic.id == CALTopicStats.topic_id)
            .where(CALTopicStats.period_date >= cutoff.date())
            .group_by(CALTopicStats.topic_id, Topic.name)
        )
        for row in result.fetchall():
            topic_freq[row.topic_id] = float(row.total)
            topic_names[row.topic_id] = row.topic_name
        
        # Get decision count and avg confidence
        decision_result = await db.execute(
            select(
                func.count(MemoryItem.id).label("count"),
                func.avg(MemoryItem.confidence).label("avg_conf")
            ).where(
                and_(
                    MemoryItem.item_type == "decision",
                    MemoryItem.created_at >= cutoff,
                    MemoryItem.status == "active"
                )
            )
        )
        decision_row = decision_result.fetchone()
        
        # Get total items
        total_result = await db.execute(
            select(func.count(MemoryItem.id)).where(
                and_(
                    MemoryItem.created_at >= cutoff,
                    MemoryItem.status == "active"
                )
            )
        )
        total = total_result.scalar() or 0
        
        # Get average quality from analyses
        quality_result = await db.execute(
            select(func.avg(CALDecisionAnalysis.overall_score)).where(
                CALDecisionAnalysis.analyzed_at >= cutoff
            )
        )
        avg_quality = quality_result.scalar() or 0.7
        
        return Baseline(
            period_days=days,
            topic_frequencies=topic_freq,
            topic_names=topic_names,
            decision_count=decision_row.count if decision_row else 0,
            avg_confidence=float(decision_row.avg_conf or 0.7) if decision_row else 0.7,
            avg_quality=float(avg_quality),
            active_topics=len(topic_freq),
            total_items=total,
        )
    
    async def _get_current(
        self,
        db: AsyncSession,
        days: int
    ) -> CurrentMetrics:
        """Get current period metrics."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Similar to baseline but for current period
        topic_freq = {}
        
        result = await db.execute(
            select(
                CALTopicStats.topic_id,
                func.sum(CALTopicStats.item_count).label("total")
            )
            .where(CALTopicStats.period_date >= cutoff.date())
            .group_by(CALTopicStats.topic_id)
        )
        for row in result.fetchall():
            topic_freq[row.topic_id] = float(row.total)
        
        decision_result = await db.execute(
            select(
                func.count(MemoryItem.id).label("count"),
                func.avg(MemoryItem.confidence).label("avg_conf")
            ).where(
                and_(
                    MemoryItem.item_type == "decision",
                    MemoryItem.created_at >= cutoff,
                    MemoryItem.status == "active"
                )
            )
        )
        decision_row = decision_result.fetchone()
        
        total_result = await db.execute(
            select(func.count(MemoryItem.id)).where(
                and_(
                    MemoryItem.created_at >= cutoff,
                    MemoryItem.status == "active"
                )
            )
        )
        total = total_result.scalar() or 0
        
        quality_result = await db.execute(
            select(func.avg(CALDecisionAnalysis.overall_score)).where(
                CALDecisionAnalysis.analyzed_at >= cutoff
            )
        )
        avg_quality = quality_result.scalar() or 0.7
        
        return CurrentMetrics(
            period_days=days,
            topic_frequencies=topic_freq,
            decision_count=decision_row.count if decision_row else 0,
            avg_confidence=float(decision_row.avg_conf or 0.7) if decision_row else 0.7,
            avg_quality=float(avg_quality),
            active_topics=len(topic_freq),
            total_items=total,
        )
    
    def _check_topics(
        self,
        baseline: Baseline,
        current: CurrentMetrics
    ) -> List[Anomaly]:
        """Check for topic-related anomalies."""
        anomalies = []
        
        for topic_id, current_freq in current.topic_frequencies.items():
            baseline_freq = baseline.topic_frequencies.get(topic_id, 0)
            topic_name = baseline.topic_names.get(topic_id, "Unknown")
            
            if baseline_freq > 0:
                # Normalize to same period
                norm_factor = current.period_days / baseline.period_days
                expected = baseline_freq * norm_factor
                change = (current_freq - expected) / expected if expected > 0 else 0
                
                if change > self.thresholds["topic_spike"]:
                    anomalies.append(Anomaly(
                        anomaly_type=AnomalyType.TOPIC_SPIKE,
                        severity=SEVERITY_MAP[AnomalyType.TOPIC_SPIKE],
                        title=f"Всплеск активности: {topic_name}",
                        description=f"Тема '{topic_name}' показала рост на {change*100:.0f}%",
                        topic_id=topic_id,
                        topic_name=topic_name,
                        baseline_value=expected,
                        current_value=current_freq,
                        deviation_percent=change * 100,
                    ))
                
                elif change < -self.thresholds["topic_drop"]:
                    anomalies.append(Anomaly(
                        anomaly_type=AnomalyType.TOPIC_DISAPPEARANCE,
                        severity=SEVERITY_MAP[AnomalyType.TOPIC_DISAPPEARANCE],
                        title=f"Снижение активности: {topic_name}",
                        description=f"Тема '{topic_name}' упала на {abs(change)*100:.0f}%",
                        topic_id=topic_id,
                        topic_name=topic_name,
                        baseline_value=expected,
                        current_value=current_freq,
                        deviation_percent=change * 100,
                    ))
        
        return anomalies
    
    def _check_decisions(
        self,
        baseline: Baseline,
        current: CurrentMetrics
    ) -> List[Anomaly]:
        """Check for decision rate anomalies."""
        anomalies = []
        
        if baseline.decision_count == 0:
            return anomalies
        
        # Normalize to weekly rate
        baseline_weekly = baseline.decision_count / baseline.period_days * 7
        current_weekly = current.decision_count / current.period_days * 7
        
        if baseline_weekly > 0:
            ratio = current_weekly / baseline_weekly
            
            if ratio >= self.thresholds["decision_surge"]:
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.DECISION_SURGE,
                    severity=SEVERITY_MAP[AnomalyType.DECISION_SURGE],
                    title="Всплеск решений",
                    description=f"Принято {current.decision_count} решений за {current.period_days} дней (норма: {baseline_weekly:.0f}/неделю)",
                    baseline_value=baseline_weekly,
                    current_value=current_weekly,
                    deviation_percent=(ratio - 1) * 100,
                ))
            
            elif ratio <= self.thresholds["decision_drought"]:
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.DECISION_DROUGHT,
                    severity=SEVERITY_MAP[AnomalyType.DECISION_DROUGHT],
                    title="Спад в принятии решений",
                    description=f"Только {current.decision_count} решений за {current.period_days} дней",
                    baseline_value=baseline_weekly,
                    current_value=current_weekly,
                    deviation_percent=(ratio - 1) * 100,
                ))
        
        return anomalies
    
    def _check_confidence(
        self,
        baseline: Baseline,
        current: CurrentMetrics
    ) -> List[Anomaly]:
        """Check for confidence shift anomalies."""
        anomalies = []
        
        if baseline.avg_confidence == 0:
            return anomalies
        
        change = (current.avg_confidence - baseline.avg_confidence) / baseline.avg_confidence
        
        if change > self.thresholds["confidence_shift"]:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.CONFIDENCE_SPIKE,
                severity=SEVERITY_MAP[AnomalyType.CONFIDENCE_SPIKE],
                title="Рост уверенности",
                description=f"Средняя уверенность выросла на {change*100:.0f}%",
                baseline_value=baseline.avg_confidence,
                current_value=current.avg_confidence,
                deviation_percent=change * 100,
            ))
        
        elif change < -self.thresholds["confidence_shift"]:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.CONFIDENCE_DROP,
                severity=SEVERITY_MAP[AnomalyType.CONFIDENCE_DROP],
                title="Падение уверенности",
                description=f"Средняя уверенность упала на {abs(change)*100:.0f}%",
                baseline_value=baseline.avg_confidence,
                current_value=current.avg_confidence,
                deviation_percent=change * 100,
            ))
        
        return anomalies
    
    async def _check_quality(
        self,
        db: AsyncSession,
        baseline: Baseline,
        current: CurrentMetrics
    ) -> List[Anomaly]:
        """Check for quality degradation."""
        anomalies = []
        
        if baseline.avg_quality == 0:
            return anomalies
        
        change = (current.avg_quality - baseline.avg_quality) / baseline.avg_quality
        
        if change < -self.thresholds["quality_drop"]:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.QUALITY_DEGRADATION,
                severity=SEVERITY_MAP[AnomalyType.QUALITY_DEGRADATION],
                title="Снижение качества решений",
                description=f"Качество решений упало на {abs(change)*100:.0f}%",
                baseline_value=baseline.avg_quality,
                current_value=current.avg_quality,
                deviation_percent=change * 100,
                suggested_action="Рекомендуется пересмотреть последние решения",
            ))
        
        return anomalies
    
    def _check_topic_diversity(
        self,
        current: CurrentMetrics
    ) -> List[Anomaly]:
        """Check for topic diversity issues."""
        anomalies = []
        
        if current.active_topics < self.thresholds["min_topic_diversity"]:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.TOPIC_NARROWING,
                severity=SEVERITY_MAP[AnomalyType.TOPIC_NARROWING],
                title="Сужение тематики",
                description=f"Активно только {current.active_topics} тем (рекомендуется минимум {self.thresholds['min_topic_diversity']})",
                current_value=float(current.active_topics),
                baseline_value=float(self.thresholds["min_topic_diversity"]),
                suggested_action="Рассмотрите расширение тематического охвата",
            ))
        
        return anomalies
    
    async def _interpret(self, anomaly: Anomaly) -> str:
        """Use LLM to generate human-readable interpretation."""
        prompt = f"""Обнаружена аномалия в паттернах мышления:

Тип: {anomaly.anomaly_type.value}
{f"Тема: {anomaly.topic_name}" if anomaly.topic_name else ""}
Изменение: {anomaly.deviation_percent:.1f}%

Дай краткую, нейтральную интерпретацию (2-3 предложения):
- Что это может означать
- Почему стоит обратить внимание

Не используй оценочные суждения, будь объективным.
Интерпретация:"""
        
        try:
            result = await groq.complete_simple(prompt)
            return result.strip()
        except Exception:
            return f"Обнаружено изменение на {anomaly.deviation_percent:.0f}% от нормы."
    
    async def save_anomalies(
        self,
        db: AsyncSession,
        anomalies: List[Anomaly]
    ) -> int:
        """Save detected anomalies to database."""
        count = 0
        
        for anomaly in anomalies:
            db_anomaly = CALAnomaly(
                id=uuid4(),
                anomaly_type=anomaly.anomaly_type.value,
                severity=anomaly.severity.value,
                title=anomaly.title,
                interpretation=anomaly.interpretation,
                suggested_action=anomaly.suggested_action,
                topic_id=anomaly.topic_id,
                memory_id=anomaly.memory_id,
                baseline_value=anomaly.baseline_value,
                current_value=anomaly.current_value,
                deviation_percent=anomaly.deviation_percent,
                status="new",
            )
            db.add(db_anomaly)
            count += 1
        
        await db.commit()
        return count


# ═══════════════════════════════════════════════════════════════════════════
# Anomaly Service
# ═══════════════════════════════════════════════════════════════════════════

class AnomalyService:
    """Service for anomaly management."""
    
    def __init__(self):
        self.detector = AnomalyDetector()
    
    async def run_detection(
        self,
        db: AsyncSession,
        baseline_days: int = 30,
        current_days: int = 7,
    ) -> Dict:
        """Run anomaly detection and save results."""
        anomalies = await self.detector.detect(db, baseline_days, current_days)
        count = await self.detector.save_anomalies(db, anomalies)
        
        return {
            "detected": len(anomalies),
            "saved": count,
            "by_severity": self._count_by_severity(anomalies),
            "by_type": self._count_by_type(anomalies),
        }
    
    def _count_by_severity(self, anomalies: List[Anomaly]) -> Dict[str, int]:
        """Count anomalies by severity."""
        counts = {}
        for a in anomalies:
            key = a.severity.value
            counts[key] = counts.get(key, 0) + 1
        return counts
    
    def _count_by_type(self, anomalies: List[Anomaly]) -> Dict[str, int]:
        """Count anomalies by type."""
        counts = {}
        for a in anomalies:
            key = a.anomaly_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts
    
    async def get_anomalies(
        self,
        db: AsyncSession,
        status: str = "new",
        severity: Optional[str] = None,
        limit: int = 20,
    ) -> List[CALAnomaly]:
        """Get anomalies from database."""
        query = select(CALAnomaly).where(CALAnomaly.status == status)
        
        if severity:
            query = query.where(CALAnomaly.severity == severity)
        
        query = query.order_by(desc(CALAnomaly.detected_at)).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def acknowledge(
        self,
        db: AsyncSession,
        anomaly_id: UUID,
        note: Optional[str] = None,
    ) -> bool:
        """Acknowledge an anomaly."""
        result = await db.execute(
            select(CALAnomaly).where(CALAnomaly.id == anomaly_id)
        )
        anomaly = result.scalar_one_or_none()
        
        if anomaly:
            anomaly.status = "acknowledged"
            anomaly.acknowledged_at = datetime.utcnow()
            await db.commit()
            return True
        return False
    
    async def resolve(
        self,
        db: AsyncSession,
        anomaly_id: UUID,
        resolution_note: Optional[str] = None,
    ) -> bool:
        """Resolve an anomaly."""
        result = await db.execute(
            select(CALAnomaly).where(CALAnomaly.id == anomaly_id)
        )
        anomaly = result.scalar_one_or_none()
        
        if anomaly:
            anomaly.status = "resolved"
            anomaly.resolved_at = datetime.utcnow()
            await db.commit()
            return True
        return False
    
    async def dismiss(
        self,
        db: AsyncSession,
        anomaly_id: UUID,
    ) -> bool:
        """Dismiss an anomaly (mark as not relevant)."""
        result = await db.execute(
            select(CALAnomaly).where(CALAnomaly.id == anomaly_id)
        )
        anomaly = result.scalar_one_or_none()
        
        if anomaly:
            anomaly.status = "dismissed"
            await db.commit()
            return True
        return False
    
    async def get_stats(
        self,
        db: AsyncSession,
    ) -> Dict:
        """Get anomaly statistics."""
        # Count by status
        status_result = await db.execute(
            select(
                CALAnomaly.status,
                func.count(CALAnomaly.id).label("count")
            ).group_by(CALAnomaly.status)
        )
        status_counts = {row.status: row.count for row in status_result.fetchall()}
        
        # Count by severity
        severity_result = await db.execute(
            select(
                CALAnomaly.severity,
                func.count(CALAnomaly.id).label("count")
            ).where(CALAnomaly.status == "new").group_by(CALAnomaly.severity)
        )
        severity_counts = {row.severity: row.count for row in severity_result.fetchall()}
        
        # Recent anomalies
        recent_result = await db.execute(
            select(func.count(CALAnomaly.id)).where(
                and_(
                    CALAnomaly.status == "new",
                    CALAnomaly.detected_at >= datetime.utcnow() - timedelta(days=7)
                )
            )
        )
        recent = recent_result.scalar() or 0
        
        return {
            "by_status": status_counts,
            "new_by_severity": severity_counts,
            "new_last_7_days": recent,
            "total_unresolved": status_counts.get("new", 0) + status_counts.get("acknowledged", 0),
        }


# Global instances
anomaly_detector = AnomalyDetector()
anomaly_service = AnomalyService()
