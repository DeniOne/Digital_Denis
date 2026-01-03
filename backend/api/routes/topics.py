"""
Digital Den — Topics API Routes
═══════════════════════════════════════════════════════════════════════════

REST API endpoints for topic management and statistics.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from memory.models import Topic
from analytics.topics import topic_statistics, TopicLoader
from core.auth import get_current_user_optional
from memory.models import User


router = APIRouter(tags=["Topics"])


# ═══════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════

class TopicResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    level: int = 0
    parent_id: Optional[UUID] = None
    item_count: int = 0

    class Config:
        from_attributes = True


class TopicActivityResponse(BaseModel):
    topic_id: UUID
    topic_name: str
    item_count: int
    decision_count: int
    insight_count: int
    avg_confidence: float


class TopicTrendResponse(BaseModel):
    topic_id: UUID
    topic_name: str
    current_count: int
    previous_count: int
    change_percent: float
    trend: str  # rising, falling, stable


class SeedResponse(BaseModel):
    topics_created: int
    message: str


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/", response_model=List[TopicResponse])
async def list_topics(
    parent_id: Optional[UUID] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """List all topics, optionally filtered by parent."""
    query = select(Topic)
    
    if parent_id:
        query = query.where(Topic.parent_id == parent_id)
    else:
        query = query.where(Topic.parent_id.is_(None))  # Root topics
    
    if not include_inactive:
        query = query.where(Topic.is_active == True)
    
    query = query.order_by(Topic.name)
    
    result = await db.execute(query)
    topics = result.scalars().all()
    
    return topics


@router.get("/tree", response_model=List[TopicResponse])
async def get_topic_tree(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get full topic tree (all topics)."""
    result = await db.execute(
        select(Topic)
        .where(Topic.is_active == True)
        .order_by(Topic.level, Topic.name)
    )
    return result.scalars().all()


@router.get("/stats/activity", response_model=List[TopicActivityResponse])
async def get_top_topics(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get most active topics."""
    activities = await topic_statistics.get_top_topics(db, days=days, limit=limit, user_id=current_user.id)
    return [
        TopicActivityResponse(
            topic_id=a.topic_id,
            topic_name=a.topic_name,
            item_count=a.item_count,
            decision_count=a.decision_count,
            insight_count=a.insight_count,
            avg_confidence=a.avg_confidence,
        )
        for a in activities
    ]


@router.get("/stats/trends", response_model=List[TopicTrendResponse])
async def get_topic_trends(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get topic trends (rising/falling)."""
    trends = await topic_statistics.get_trends(db, days=days, limit=limit, user_id=current_user.id)
    return [
        TopicTrendResponse(
            topic_id=t.topic_id,
            topic_name=t.topic_name,
            current_count=t.current_count,
            previous_count=t.previous_count,
            change_percent=t.change_percent,
            trend=t.trend,
        )
        for t in trends
    ]


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get single topic by ID."""
    result = await db.execute(
        select(Topic).where(Topic.id == topic_id)
    )
    topic = result.scalar_one_or_none()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return topic


@router.get("/{topic_id}/activity", response_model=TopicActivityResponse)
async def get_topic_activity(
    topic_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get activity metrics for a specific topic."""
    activity = await topic_statistics.get_activity(db, topic_id, days=days, user_id=current_user.id)
    
    if not activity:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return TopicActivityResponse(
        topic_id=activity.topic_id,
        topic_name=activity.topic_name,
        item_count=activity.item_count,
        decision_count=activity.decision_count,
        insight_count=activity.insight_count,
        avg_confidence=activity.avg_confidence,
    )


@router.post("/seed", response_model=SeedResponse)
async def seed_default_topics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Seed default topics from config file."""
    import os
    
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "ai", "config", "topics.yaml"
    )
    
    if not os.path.exists(config_path):
        raise HTTPException(
            status_code=404, 
            detail=f"Topics config not found at {config_path}"
        )
    
    count = await TopicLoader.seed_topics(db, config_path)
    
    return SeedResponse(
        topics_created=count,
        message=f"Successfully seeded {count} topics"
    )
