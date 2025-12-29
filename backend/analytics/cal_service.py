"""
Digital Denis — CAL Service
═══════════════════════════════════════════════════════════════════════════

Cognitive Analytics Layer main service.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.cal_models import (
    CALTopicStats, CALGraphNode, CALGraphEdge,
    CALDecisionAnalysis, CALAnomaly, CALHealthSnapshot
)
from analytics.topics import topic_extractor, topic_statistics
from memory.models import MemoryItem, Topic
from llm.groq import groq


# ═══════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class TopicTrend:
    """Topic trend data."""
    topic_id: UUID
    topic_name: str
    current_count: int
    previous_count: int
    change_percent: float
    trend: str  # rising, falling, stable


@dataclass
class GraphData:
    """Mind map graph structure."""
    nodes: List[Dict]
    edges: List[Dict]
    clusters: List[Dict] = field(default_factory=list)


@dataclass
class Anomaly:
    """Anomaly alert."""
    id: UUID
    anomaly_type: str
    severity: str
    title: str
    interpretation: str
    detected_at: datetime
    status: str


@dataclass
class CognitiveHealthReport:
    """Overall cognitive health report."""
    date: date
    overall_score: float
    decision_quality: float
    memory_diversity: float
    thinking_consistency: float
    active_topics: int
    total_memories: int
    anomalies_count: int
    recommendations: List[str]


# ═══════════════════════════════════════════════════════════════════════════
# CAL Service
# ═══════════════════════════════════════════════════════════════════════════

class CALService:
    """
    Cognitive Analytics Layer Service.
    
    Provides:
    - Topic trend analysis
    - Mind map graph building
    - Decision quality analysis
    - Anomaly detection
    - Cognitive health reports
    """
    
    def __init__(self):
        self.min_confidence = 0.5
    
    # ═══════════════════════════════════════════════════════════════════════
    # Memory Layer Integration (hooks)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def on_memory_created(self, db: AsyncSession, memory_id: UUID) -> None:
        """
        Called when a new memory item is created.
        Triggers appropriate CAL processing.
        """
        # Get the memory item
        result = await db.execute(
            select(MemoryItem).where(MemoryItem.id == memory_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            return
        
        # Extract and assign topics
        topics = await topic_extractor.extract(item.content)
        for topic in topics:
            if topic.topic_id:
                await self._update_topic_stats(db, topic.topic_id)
        
        # Create graph node
        await self._create_graph_node(db, item)
        
        # If decision, queue analysis
        if item.item_type == "decision":
            await self.analyze_decision(db, memory_id)
        
        await db.commit()
    
    # ═══════════════════════════════════════════════════════════════════════
    # Topic Trends
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_topic_trends(
        self,
        db: AsyncSession,
        days: int = 30
    ) -> List[TopicTrend]:
        """Get topic activity trends."""
        return await topic_statistics.get_trends(db, days=days)
    
    async def _update_topic_stats(
        self, 
        db: AsyncSession, 
        topic_id: UUID
    ) -> None:
        """Update daily topic statistics."""
        today = date.today()
        
        # Check if stats exist for today
        result = await db.execute(
            select(CALTopicStats).where(
                and_(
                    CALTopicStats.topic_id == topic_id,
                    CALTopicStats.period_date == today
                )
            )
        )
        stats = result.scalar_one_or_none()
        
        if stats:
            stats.item_count += 1
        else:
            stats = CALTopicStats(
                id=uuid4(),
                topic_id=topic_id,
                period_date=today,
                item_count=1,
            )
            db.add(stats)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Mind Map Graph
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_mind_map(
        self,
        db: AsyncSession,
        topic_id: Optional[UUID] = None,
        days: int = 30,
        limit: int = 100
    ) -> GraphData:
        """Get mind map graph data for visualization."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get nodes
        query = select(CALGraphNode).where(
            CALGraphNode.created_at > cutoff
        )
        
        if topic_id:
            query = query.where(CALGraphNode.topic_id == topic_id)
        
        query = query.order_by(desc(CALGraphNode.importance_score)).limit(limit)
        
        result = await db.execute(query)
        nodes = result.scalars().all()
        node_ids = [n.id for n in nodes]
        
        # Get edges for these nodes
        edge_result = await db.execute(
            select(CALGraphEdge).where(
                CALGraphEdge.source_id.in_(node_ids) |
                CALGraphEdge.target_id.in_(node_ids)
            )
        )
        edges = edge_result.scalars().all()
        
        return GraphData(
            nodes=[
                {
                    "id": str(n.id),
                    "label": n.label,
                    "type": n.node_type,
                    "x": n.x_pos,
                    "y": n.y_pos,
                    "cluster": n.cluster_id,
                    "importance": n.importance_score,
                }
                for n in nodes
            ],
            edges=[
                {
                    "id": str(e.id),
                    "source": str(e.source_id),
                    "target": str(e.target_id),
                    "type": e.edge_type,
                    "weight": e.weight,
                }
                for e in edges
            ],
        )
    
    async def _create_graph_node(
        self, 
        db: AsyncSession, 
        item: MemoryItem
    ) -> CALGraphNode:
        """Create a graph node for memory item."""
        node = CALGraphNode(
            id=uuid4(),
            memory_id=item.id,
            node_type=item.item_type,
            label=item.summary or item.content[:100],
            importance_score=item.confidence or 0.5,
        )
        db.add(node)
        return node
    
    async def find_connections(
        self,
        db: AsyncSession,
        node_id: UUID,
        similarity_threshold: float = 0.7
    ) -> List[CALGraphEdge]:
        """Find and create connections between nodes."""
        from memory.semantic import semantic_memory
        
        # Get the node's memory item
        result = await db.execute(
            select(CALGraphNode).where(CALGraphNode.id == node_id)
        )
        node = result.scalar_one_or_none()
        
        if not node or not node.memory_id:
            return []
        
        # Find similar memories
        similar = await semantic_memory.find_similar(db, node.memory_id, limit=5)
        
        edges = []
        for similar_item, similarity in similar:
            if similarity >= similarity_threshold:
                # Find corresponding node
                node_result = await db.execute(
                    select(CALGraphNode).where(CALGraphNode.memory_id == similar_item.id)
                )
                target_node = node_result.scalar_one_or_none()
                
                if target_node:
                    edge = CALGraphEdge(
                        id=uuid4(),
                        source_id=node_id,
                        target_id=target_node.id,
                        edge_type="relates_to",
                        weight=similarity,
                        confidence=similarity,
                    )
                    db.add(edge)
                    edges.append(edge)
        
        return edges
    
    # ═══════════════════════════════════════════════════════════════════════
    # Decision Analysis
    # ═══════════════════════════════════════════════════════════════════════
    
    async def analyze_decision(
        self,
        db: AsyncSession,
        decision_id: UUID
    ) -> Optional[CALDecisionAnalysis]:
        """Analyze a decision's quality and risks."""
        # Get decision
        result = await db.execute(
            select(MemoryItem).where(
                and_(
                    MemoryItem.id == decision_id,
                    MemoryItem.item_type == "decision"
                )
            )
        )
        decision = result.scalar_one_or_none()
        
        if not decision:
            return None
        
        # Analyze with LLM
        prompt = f"""Проанализируй это решение и оцени его качество.

Решение:
{decision.content}

{f"Структура: {decision.structured_data}" if decision.structured_data else ""}

Ответь в JSON:
{{
    "strong_points": ["сильная сторона 1"],
    "weak_points": ["слабая сторона 1"],
    "risks": ["риск 1"],
    "missing_info": ["чего не хватает"],
    "clarity_score": 0.0-1.0,
    "completeness_score": 0.0-1.0,
    "risk_level": "low|medium|high",
    "recommendations": ["рекомендация 1"]
}}

JSON:"""
        
        try:
            result_text = await groq.complete_simple(prompt)
            analysis_data = self._parse_analysis(result_text)
            
            analysis = CALDecisionAnalysis(
                id=uuid4(),
                decision_id=decision_id,
                strong_points=analysis_data.get("strong_points", []),
                weak_points=analysis_data.get("weak_points", []),
                risks=analysis_data.get("risks", []),
                missing_info=analysis_data.get("missing_info", []),
                clarity_score=analysis_data.get("clarity_score", 0.5),
                completeness_score=analysis_data.get("completeness_score", 0.5),
                risk_level=analysis_data.get("risk_level", "medium"),
                overall_score=(
                    analysis_data.get("clarity_score", 0.5) +
                    analysis_data.get("completeness_score", 0.5)
                ) / 2,
                recommendations=analysis_data.get("recommendations", []),
            )
            db.add(analysis)
            
            # Create anomaly if high risk
            if analysis.risk_level == "high":
                await self._create_anomaly(
                    db,
                    anomaly_type="high_risk_decision",
                    severity="high",
                    title=f"Решение с высоким риском",
                    interpretation=f"Обнаружено решение с высоким уровнем риска: {decision.content[:100]}",
                    memory_id=decision_id,
                )
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing decision: {e}")
            return None
    
    def _parse_analysis(self, response: str) -> Dict:
        """Parse LLM analysis response."""
        import json
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return {}
    
    # ═══════════════════════════════════════════════════════════════════════
    # Anomaly Detection
    # ═══════════════════════════════════════════════════════════════════════
    
    async def detect_anomalies(
        self,
        db: AsyncSession,
        baseline_days: int = 30,
        current_days: int = 7
    ) -> List[CALAnomaly]:
        """Detect anomalies by comparing current period with baseline."""
        anomalies = []
        
        # Get topic trends
        trends = await topic_statistics.get_trends(db, days=baseline_days)
        
        for trend in trends:
            # Detect significant changes
            if abs(trend.change_percent) > 50:
                if trend.change_percent > 50:
                    anomaly_type = "topic_spike"
                    interpretation = f"Резкий рост активности по теме '{trend.topic_name}'"
                else:
                    anomaly_type = "topic_drop"
                    interpretation = f"Резкое снижение активности по теме '{trend.topic_name}'"
                
                anomaly = await self._create_anomaly(
                    db,
                    anomaly_type=anomaly_type,
                    severity="medium" if abs(trend.change_percent) < 100 else "high",
                    title=f"Изменение в теме: {trend.topic_name}",
                    interpretation=interpretation,
                    topic_id=trend.topic_id,
                    baseline_value=float(trend.previous_count),
                    current_value=float(trend.current_count),
                    deviation_percent=trend.change_percent,
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    async def get_anomalies(
        self,
        db: AsyncSession,
        status: str = "new",
        limit: int = 20
    ) -> List[Anomaly]:
        """Get current anomalies."""
        result = await db.execute(
            select(CALAnomaly)
            .where(CALAnomaly.status == status)
            .order_by(desc(CALAnomaly.detected_at))
            .limit(limit)
        )
        
        return [
            Anomaly(
                id=a.id,
                anomaly_type=a.anomaly_type,
                severity=a.severity,
                title=a.title,
                interpretation=a.interpretation,
                detected_at=a.detected_at,
                status=a.status,
            )
            for a in result.scalars().all()
        ]
    
    async def _create_anomaly(
        self,
        db: AsyncSession,
        anomaly_type: str,
        severity: str,
        title: str,
        interpretation: str,
        topic_id: Optional[UUID] = None,
        memory_id: Optional[UUID] = None,
        baseline_value: Optional[float] = None,
        current_value: Optional[float] = None,
        deviation_percent: Optional[float] = None,
    ) -> CALAnomaly:
        """Create an anomaly alert."""
        anomaly = CALAnomaly(
            id=uuid4(),
            anomaly_type=anomaly_type,
            severity=severity,
            title=title,
            interpretation=interpretation,
            topic_id=topic_id,
            memory_id=memory_id,
            baseline_value=baseline_value,
            current_value=current_value,
            deviation_percent=deviation_percent,
        )
        db.add(anomaly)
        return anomaly
    
    async def acknowledge_anomaly(
        self,
        db: AsyncSession,
        anomaly_id: UUID
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
    
    # ═══════════════════════════════════════════════════════════════════════
    # Cognitive Health
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_cognitive_health(
        self,
        db: AsyncSession
    ) -> CognitiveHealthReport:
        """Get overall cognitive health report."""
        today = date.today()
        days_back = 7
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        
        # Count memories
        memory_result = await db.execute(
            select(func.count(MemoryItem.id)).where(
                and_(
                    MemoryItem.status == "active",
                    MemoryItem.created_at > cutoff
                )
            )
        )
        total_memories = memory_result.scalar() or 0
        
        # Count decisions
        decision_result = await db.execute(
            select(func.count(MemoryItem.id)).where(
                and_(
                    MemoryItem.item_type == "decision",
                    MemoryItem.status == "active",
                    MemoryItem.created_at > cutoff
                )
            )
        )
        decisions = decision_result.scalar() or 0
        
        # Count insights
        insight_result = await db.execute(
            select(func.count(MemoryItem.id)).where(
                and_(
                    MemoryItem.item_type == "insight",
                    MemoryItem.status == "active",
                    MemoryItem.created_at > cutoff
                )
            )
        )
        insights = insight_result.scalar() or 0
        
        # Count active topics
        topic_result = await db.execute(
            select(func.count(Topic.id)).where(Topic.is_active == True)
        )
        active_topics = topic_result.scalar() or 0
        
        # Count unresolved anomalies
        anomaly_result = await db.execute(
            select(func.count(CALAnomaly.id)).where(
                CALAnomaly.status.in_(["new", "acknowledged"])
            )
        )
        anomalies = anomaly_result.scalar() or 0
        
        # Calculate scores (simplified)
        decision_quality = min(1.0, decisions / max(1, total_memories) * 2) * 100
        memory_diversity = min(1.0, insights / max(1, decisions + 1)) * 100
        thinking_consistency = max(0, 100 - anomalies * 10)
        overall = (decision_quality + memory_diversity + thinking_consistency) / 3
        
        # Generate recommendations
        recommendations = []
        if decisions == 0:
            recommendations.append("Попробуйте принять несколько решений для лучшего отслеживания")
        if insights < decisions:
            recommendations.append("Уделите больше времени рефлексии и инсайтам")
        if anomalies > 3:
            recommendations.append("Обратите внимание на накопившиеся аномалии")
        
        return CognitiveHealthReport(
            date=today,
            overall_score=overall,
            decision_quality=decision_quality,
            memory_diversity=memory_diversity,
            thinking_consistency=thinking_consistency,
            active_topics=active_topics,
            total_memories=total_memories,
            anomalies_count=anomalies,
            recommendations=recommendations,
        )
    
    async def create_health_snapshot(
        self,
        db: AsyncSession
    ) -> CALHealthSnapshot:
        """Create a health snapshot for today."""
        report = await self.get_cognitive_health(db)
        
        snapshot = CALHealthSnapshot(
            id=uuid4(),
            snapshot_date=report.date,
            total_memories=report.total_memories,
            active_topics=report.active_topics,
            decisions_made=0,  # Would need to track
            insights_captured=0,
            decision_quality_avg=report.decision_quality,
            memory_diversity_score=report.memory_diversity,
            thinking_consistency_score=report.thinking_consistency,
            overall_health_score=report.overall_score,
            anomalies_count=report.anomalies_count,
            unresolved_anomalies=report.anomalies_count,
        )
        db.add(snapshot)
        await db.commit()
        return snapshot


# Global instance
cal_service = CALService()
