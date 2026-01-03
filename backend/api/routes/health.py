"""
Digital Den — Health API Routes
═══════════════════════════════════════════════════════════════════════════

REST API endpoints for system health and cognitive health.
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db


router = APIRouter(tags=["Health"])


# ═══════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════

class SystemHealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: int
    database: str
    redis: str
    timestamp: str


class CognitiveHealthResponse(BaseModel):
    overall_score: float
    decision_quality: float
    memory_diversity: float
    thinking_consistency: float
    active_topics: int
    total_memories: int
    anomalies_count: int
    last_activity: str


# ═══════════════════════════════════════════════════════════════════════════
# State
# ═══════════════════════════════════════════════════════════════════════════

START_TIME = datetime.utcnow()


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/", response_model=SystemHealthResponse)
async def get_system_health(
    db: AsyncSession = Depends(get_db)
):
    """Get system health status."""
    uptime = (datetime.utcnow() - START_TIME).total_seconds()
    
    # Check database
    db_status = "ok"
    try:
        await db.execute(select(func.now()))
    except Exception:
        db_status = "error"
    
    # Check Redis (placeholder)
    redis_status = "ok"
    
    return SystemHealthResponse(
        status="healthy" if db_status == "ok" and redis_status == "ok" else "degraded",
        version="1.0.0",
        uptime_seconds=int(uptime),
        database=db_status,
        redis=redis_status,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/cognitive", response_model=CognitiveHealthResponse)
async def get_cognitive_health(
    db: AsyncSession = Depends(get_db)
):
    """Get cognitive health metrics."""
    from memory.models import MemoryItem, Topic
    from analytics.cal_models import CALDecisionAnalysis, CALAnomaly
    from datetime import timedelta
    
    # Total memories
    mem_result = await db.execute(
        select(func.count(MemoryItem.id)).where(MemoryItem.status == "active")
    )
    total_memories = mem_result.scalar() or 0
    
    # Active topics
    topic_result = await db.execute(
        select(func.count(Topic.id)).where(Topic.is_active == True)
    )
    active_topics = topic_result.scalar() or 0
    
    # Decision quality (average)
    quality_result = await db.execute(
        select(func.avg(CALDecisionAnalysis.overall_score))
    )
    decision_quality = quality_result.scalar() or 0.7
    
    # Anomalies count (unresolved)
    anomaly_result = await db.execute(
        select(func.count(CALAnomaly.id)).where(CALAnomaly.status == "new")
    )
    anomalies_count = anomaly_result.scalar() or 0
    
    # Last activity
    last_result = await db.execute(
        select(MemoryItem.created_at)
        .order_by(MemoryItem.created_at.desc())
        .limit(1)
    )
    last_activity = last_result.scalar()
    
    # Calculate scores
    memory_diversity = min(1.0, active_topics / 10.0) if active_topics > 0 else 0.5
    thinking_consistency = 0.75  # Placeholder
    overall_score = (decision_quality * 0.4 + memory_diversity * 0.3 + thinking_consistency * 0.3)
    
    return CognitiveHealthResponse(
        overall_score=round(overall_score, 2),
        decision_quality=round(float(decision_quality), 2),
        memory_diversity=round(memory_diversity, 2),
        thinking_consistency=round(thinking_consistency, 2),
        active_topics=active_topics,
        total_memories=total_memories,
        anomalies_count=anomalies_count,
        last_activity=last_activity.isoformat() if last_activity else "",
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint for monitoring."""
    return {"status": "pong", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db)
):
    """Kubernetes-style readiness check."""
    try:
        await db.execute(select(func.now()))
        return {"ready": True}
    except Exception as e:
        return {"ready": False, "error": str(e)}


@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness check."""
    return {"alive": True}
