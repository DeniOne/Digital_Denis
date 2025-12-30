"""
Digital Denis — Anomaly Detection API Routes
═══════════════════════════════════════════════════════════════════════════

REST API endpoints for anomaly detection and management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from analytics.anomalies import anomaly_service
from core.auth import get_current_user_optional
from memory.models import User


router = APIRouter(tags=["Anomalies"])


# ═══════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════

class AnomalyResponse(BaseModel):
    id: UUID
    anomaly_type: str
    severity: str
    title: str
    interpretation: Optional[str] = None
    suggested_action: Optional[str] = None
    topic_id: Optional[UUID] = None
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    deviation_percent: Optional[float] = None
    status: str
    detected_at: str


class DetectionResultResponse(BaseModel):
    detected: int
    saved: int
    by_severity: dict
    by_type: dict


class AnomalyStatsResponse(BaseModel):
    by_status: dict
    new_by_severity: dict
    new_last_7_days: int
    total_unresolved: int


class ActionResponse(BaseModel):
    success: bool
    anomaly_id: UUID
    new_status: str


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/", response_model=List[AnomalyResponse])
async def list_anomalies(
    status: str = Query("new", regex="^(new|acknowledged|resolved|dismissed)$"),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """List anomalies with optional filtering."""
    anomalies = await anomaly_service.get_anomalies(
        db,
        user_id=current_user.id,
        status=status,
        severity=severity,
        limit=limit,
    )
    
    return [
        AnomalyResponse(
            id=a.id,
            anomaly_type=a.anomaly_type,
            severity=a.severity,
            title=a.title or "",
            interpretation=a.interpretation,
            suggested_action=a.suggested_action,
            topic_id=a.topic_id,
            baseline_value=a.baseline_value,
            current_value=a.current_value,
            deviation_percent=a.deviation_percent,
            status=a.status,
            detected_at=a.detected_at.isoformat() if a.detected_at else "",
        )
        for a in anomalies
    ]


@router.post("/detect", response_model=DetectionResultResponse)
async def run_anomaly_detection(
    baseline_days: int = Query(30, ge=7, le=90),
    current_days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """
    Run anomaly detection.
    
    Compares current period against baseline to detect anomalies.
    """
    result = await anomaly_service.run_detection(
        db,
        user_id=current_user.id,
        baseline_days=baseline_days,
        current_days=current_days,
    )
    
    return DetectionResultResponse(**result)


@router.get("/stats", response_model=AnomalyStatsResponse)
async def get_anomaly_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get anomaly statistics."""
    stats = await anomaly_service.get_stats(db, user_id=current_user.id)
    return AnomalyStatsResponse(**stats)


@router.get("/{anomaly_id}", response_model=AnomalyResponse)
async def get_anomaly(
    anomaly_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get a specific anomaly by ID."""
    from analytics.cal_models import CALAnomaly
    from sqlalchemy import select
    
    result = await db.execute(
        select(CALAnomaly).where(
            and_(
                CALAnomaly.id == anomaly_id,
                CALAnomaly.user_id == current_user.id
            )
        )
    )
    anomaly = result.scalar_one_or_none()
    
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    return AnomalyResponse(
        id=anomaly.id,
        anomaly_type=anomaly.anomaly_type,
        severity=anomaly.severity,
        title=anomaly.title or "",
        interpretation=anomaly.interpretation,
        suggested_action=anomaly.suggested_action,
        topic_id=anomaly.topic_id,
        baseline_value=anomaly.baseline_value,
        current_value=anomaly.current_value,
        deviation_percent=anomaly.deviation_percent,
        status=anomaly.status,
        detected_at=anomaly.detected_at.isoformat() if anomaly.detected_at else "",
    )


@router.post("/{anomaly_id}/acknowledge", response_model=ActionResponse)
async def acknowledge_anomaly(
    anomaly_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Acknowledge an anomaly."""
    success = await anomaly_service.acknowledge(db, anomaly_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    return ActionResponse(
        success=True,
        anomaly_id=anomaly_id,
        new_status="acknowledged",
    )


@router.post("/{anomaly_id}/resolve", response_model=ActionResponse)
async def resolve_anomaly(
    anomaly_id: UUID,
    resolution_note: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Resolve an anomaly."""
    success = await anomaly_service.resolve(db, anomaly_id, resolution_note)
    
    if not success:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    return ActionResponse(
        success=True,
        anomaly_id=anomaly_id,
        new_status="resolved",
    )


@router.post("/{anomaly_id}/dismiss", response_model=ActionResponse)
async def dismiss_anomaly(
    anomaly_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Dismiss an anomaly (mark as not relevant)."""
    success = await anomaly_service.dismiss(db, anomaly_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    return ActionResponse(
        success=True,
        anomaly_id=anomaly_id,
        new_status="dismissed",
    )


@router.get("/types/summary")
async def get_anomaly_type_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get summary by anomaly type."""
    from analytics.cal_models import CALAnomaly
    from sqlalchemy import select, func
    
    result = await db.execute(
        select(
            CALAnomaly.anomaly_type,
            func.count(CALAnomaly.id).label("total"),
            func.sum(func.cast(CALAnomaly.status == "new", type_=None)).label("new_count")
        ).where(CALAnomaly.user_id == current_user.id).group_by(CALAnomaly.anomaly_type)
    )
    
    return [
        {
            "type": row.anomaly_type,
            "total": row.total,
            "new": int(row.new_count or 0),
        }
        for row in result.fetchall()
    ]
