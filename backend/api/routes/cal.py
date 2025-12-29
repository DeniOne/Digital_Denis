"""
Digital Denis — CAL API Routes
═══════════════════════════════════════════════════════════════════════════

REST API endpoints for Cognitive Analytics Layer.
"""

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from analytics.cal_service import cal_service


router = APIRouter(prefix="/cal", tags=["Cognitive Analytics"])


# ═══════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════

class TopicTrendResponse(BaseModel):
    topic_id: UUID
    topic_name: str
    current_count: int
    previous_count: int
    change_percent: float
    trend: str


class GraphNodeResponse(BaseModel):
    id: str
    label: str
    type: str
    x: Optional[float] = None
    y: Optional[float] = None
    cluster: Optional[int] = None
    importance: float


class GraphEdgeResponse(BaseModel):
    id: str
    source: str
    target: str
    type: str
    weight: float


class GraphDataResponse(BaseModel):
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]


class AnomalyResponse(BaseModel):
    id: UUID
    anomaly_type: str
    severity: str
    title: str
    interpretation: str
    detected_at: str
    status: str


class CognitiveHealthResponse(BaseModel):
    date: date
    overall_score: float
    decision_quality: float
    memory_diversity: float
    thinking_consistency: float
    active_topics: int
    total_memories: int
    anomalies_count: int
    recommendations: List[str]


class AcknowledgeResponse(BaseModel):
    success: bool
    anomaly_id: UUID


# ═══════════════════════════════════════════════════════════════════════════
# Topic Trends
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/trends", response_model=List[TopicTrendResponse])
async def get_topic_trends(
    days: int = Query(30, ge=7, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get topic activity trends."""
    trends = await cal_service.get_topic_trends(db, days=days)
    return [
        TopicTrendResponse(
            topic_id=t.topic_id,
            topic_name=t.topic_name,
            current_count=t.current_count,
            previous_count=t.previous_count,
            change_percent=t.change_percent,
            trend=t.trend,
        )
        for t in trends[:limit]
    ]


# ═══════════════════════════════════════════════════════════════════════════
# Mind Map Graph
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/graph", response_model=GraphDataResponse)
async def get_mind_map(
    topic_id: Optional[UUID] = None,
    days: int = Query(30, ge=7, le=365),
    limit: int = Query(100, ge=10, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Get mind map graph data for visualization."""
    graph = await cal_service.get_mind_map(db, topic_id=topic_id, days=days, limit=limit)
    return GraphDataResponse(
        nodes=[
            GraphNodeResponse(**n) for n in graph.nodes
        ],
        edges=[
            GraphEdgeResponse(**e) for e in graph.edges
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# Anomalies
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/anomalies", response_model=List[AnomalyResponse])
async def get_anomalies(
    status: str = Query("new", regex="^(new|acknowledged|resolved)$"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get current anomalies."""
    anomalies = await cal_service.get_anomalies(db, status=status, limit=limit)
    return [
        AnomalyResponse(
            id=a.id,
            anomaly_type=a.anomaly_type,
            severity=a.severity,
            title=a.title,
            interpretation=a.interpretation,
            detected_at=a.detected_at.isoformat(),
            status=a.status,
        )
        for a in anomalies
    ]


@router.post("/anomalies/{anomaly_id}/acknowledge", response_model=AcknowledgeResponse)
async def acknowledge_anomaly(
    anomaly_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an anomaly."""
    success = await cal_service.acknowledge_anomaly(db, anomaly_id)
    return AcknowledgeResponse(success=success, anomaly_id=anomaly_id)


@router.post("/anomalies/detect")
async def trigger_anomaly_detection(
    db: AsyncSession = Depends(get_db)
):
    """Trigger anomaly detection manually."""
    anomalies = await cal_service.detect_anomalies(db)
    await db.commit()
    return {
        "status": "ok",
        "anomalies_detected": len(anomalies),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Cognitive Health
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/health", response_model=CognitiveHealthResponse)
async def get_cognitive_health(
    db: AsyncSession = Depends(get_db)
):
    """Get overall cognitive health report."""
    report = await cal_service.get_cognitive_health(db)
    return CognitiveHealthResponse(
        date=report.date,
        overall_score=report.overall_score,
        decision_quality=report.decision_quality,
        memory_diversity=report.memory_diversity,
        thinking_consistency=report.thinking_consistency,
        active_topics=report.active_topics,
        total_memories=report.total_memories,
        anomalies_count=report.anomalies_count,
        recommendations=report.recommendations,
    )


@router.post("/health/snapshot")
async def create_health_snapshot(
    db: AsyncSession = Depends(get_db)
):
    """Create a health snapshot for today."""
    snapshot = await cal_service.create_health_snapshot(db)
    return {
        "status": "ok",
        "snapshot_id": str(snapshot.id),
        "overall_score": snapshot.overall_health_score,
    }
