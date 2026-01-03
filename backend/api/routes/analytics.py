"""
Digital Den — Analytics API
═══════════════════════════════════════════════════════════════════════════

Endpoints for dashboard metrics and visualizations.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from uuid import UUID

from db.database import get_db
from analytics.service import analytics_service
from analytics.topics import topic_statistics
from analytics.sentiment import sentiment_service
from analytics.anomalies import anomaly_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/summary")
async def get_analytics_summary(
    user_id: UUID,  # Should be from auth
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get high-level statistics summary."""
    return await analytics_service.get_summary(db, user_id, days=days)

@router.get("/activity")
async def get_activity_data(
    user_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get daily activity counts for charts."""
    return await analytics_service.get_activity_timeline(db, user_id, days=days)

@router.get("/heatmap")
async def get_heatmap_data(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get yearly activity for heatmap visualization."""
    return await analytics_service.get_heatmap_data(db, user_id)

@router.get("/trends")
async def get_topic_trends(
    user_id: UUID,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get rising and falling topic trends."""
    return await topic_statistics.get_trends(db, days=days, user_id=user_id)


@router.get("/mood")
async def get_daily_mood(
    user_id: UUID,
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get daily mood tracking based on memory sentiment."""
    return await sentiment_service.get_daily_mood(db, user_id, days=days)


@router.post("/anomalies/detect")
async def detect_anomalies(
    baseline_days: int = 30,
    current_days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """Run anomaly detection engine."""
    return await anomaly_service.run_detection(db, baseline_days, current_days)


@router.get("/reports/weekly")
async def get_weekly_report(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Generate weekly summary report."""
    # Stub for now
    return {
        "title": "Weekly Insight Report",
        "generated_at": "2025-12-31T12:00:00Z",
        "content_markdown": "# Weekly Summary\n\n**Activity:** High\n**Mood:** Positive\n\n- Topic A grew by 20%\n- 3 Decisions made."
    }
