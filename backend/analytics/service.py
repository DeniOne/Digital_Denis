"""
Digital Den — Analytics Service
═══════════════════════════════════════════════════════════════════════════

Core metrics calculation and data aggregation for the dashboard.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import MemoryItem, Topic, MemoryTopic
from analytics.topics import topic_statistics

class AnalyticsService:
    """
    Calculates metrics for personal dashboard.
    """
    
    async def get_summary(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get high-level summary of user memories.
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        # 1. Total counts
        total_stmt = (
            select(func.count(MemoryItem.id))
            .where(MemoryItem.user_id == user_id)
            .where(MemoryItem.status == 'active')
            .where(MemoryItem.created_at >= since)
        )
        total = await db.scalar(total_stmt) or 0
        
        # 2. Breakdown by type
        type_stmt = (
            select(MemoryItem.item_type, func.count(MemoryItem.id))
            .where(MemoryItem.user_id == user_id)
            .where(MemoryItem.status == 'active')
            .where(MemoryItem.created_at >= since)
            .group_by(MemoryItem.item_type)
        )
        type_res = await db.execute(type_stmt)
        by_type = {row[0]: row[1] for row in type_res.fetchall()}
        
        # 3. Top topics (reusing existing topic_statistics)
        top_topics = await topic_statistics.get_top_topics(db, days=days, user_id=user_id, limit=5)
        
        # 4. Activity streak (simplified)
        streak = await self._calculate_streak(db, user_id)
        
        return {
            "total_memories": total,
            "by_type": by_type,
            "top_topics": [
                {"id": str(t.topic_id), "name": t.topic_name, "count": t.item_count}
                for t in top_topics
            ],
            "streak": streak,
            "period_days": days
        }
    
    async def get_activity_timeline(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get daily activity counts for line/area charts.
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        stmt = (
            select(func.date(MemoryItem.created_at).label('date'), func.count(MemoryItem.id))
            .where(MemoryItem.user_id == user_id)
            .where(MemoryItem.status == 'active')
            .where(MemoryItem.created_at >= since)
            .group_by(func.date(MemoryItem.created_at))
            .order_by(text('date'))
        )
        
        result = await db.execute(stmt)
        return [{"date": str(row[0]), "count": row[1]} for row in result.fetchall()]

    async def get_heatmap_data(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get 365 days of activity for heatmaps.
        """
        return await self.get_activity_timeline(db, user_id, days=365)

    async def _calculate_streak(self, db: AsyncSession, user_id: UUID) -> int:
        """
        Calculate current activity streak in days.
        """
        # Simplified streak calculation
        stmt = (
            select(func.date(MemoryItem.created_at).label('date'))
            .where(MemoryItem.user_id == user_id)
            .where(MemoryItem.status == 'active')
            .group_by(func.date(MemoryItem.created_at))
            .order_by(text('date DESC'))
            .limit(30)
        )
        
        result = await db.execute(stmt)
        dates = [row[0] for row in result.fetchall()]
        
        if not dates:
            return 0
            
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        if dates[0] not in [today, yesterday]:
            return 0
            
        streak = 0
        current_check = dates[0]
        
        for d in dates:
            if d == current_check:
                streak += 1
                current_check -= timedelta(days=1)
            else:
                break
                
        return streak

analytics_service = AnalyticsService()
