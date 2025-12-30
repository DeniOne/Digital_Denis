"""
Digital Denis — Topic Intelligence Engine
═══════════════════════════════════════════════════════════════════════════

Automatic topic extraction and classification for memory items.
"""

import json
import yaml
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import Topic, MemoryItem, MemoryTopic
from llm.groq import groq  # Use cheap model for classification


# ═══════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class TopicAssignment:
    """Topic assignment with confidence score."""
    topic_slug: str
    confidence: float
    topic_id: Optional[UUID] = None


@dataclass
class TopicActivity:
    """Activity metrics for a topic."""
    topic_id: UUID
    topic_name: str
    item_count: int
    decision_count: int
    insight_count: int
    avg_confidence: float
    last_activity: Optional[datetime] = None


@dataclass
class TopicTrend:
    """Topic trend data."""
    topic_id: UUID
    topic_name: str
    current_count: int
    previous_count: int
    change_percent: float
    trend: str  # "rising", "falling", "stable"


# ═══════════════════════════════════════════════════════════════════════════
# Topic Tree Manager
# ═══════════════════════════════════════════════════════════════════════════

class TopicTree:
    """Manages topic hierarchy."""
    
    def __init__(self):
        self.topics: Dict[str, Topic] = {}
        self.hierarchy: Dict[str, List[str]] = {}  # parent -> children
    
    async def load_from_db(self, db: AsyncSession) -> None:
        """Load topics from database."""
        result = await db.execute(
            select(Topic).where(Topic.is_active == True)
        )
        topics = result.scalars().all()
        
        for topic in topics:
            self.topics[topic.slug] = topic
            if topic.parent_id:
                parent_slug = next(
                    (t.slug for t in topics if t.id == topic.parent_id),
                    None
                )
                if parent_slug:
                    if parent_slug not in self.hierarchy:
                        self.hierarchy[parent_slug] = []
                    self.hierarchy[parent_slug].append(topic.slug)
    
    def exists(self, slug: str) -> bool:
        """Check if topic exists."""
        return slug in self.topics
    
    def get(self, slug: str) -> Optional[Topic]:
        """Get topic by slug."""
        return self.topics.get(slug)
    
    def get_all(self) -> List[Topic]:
        """Get all topics."""
        return list(self.topics.values())
    
    def get_children(self, slug: str) -> List[Topic]:
        """Get child topics."""
        child_slugs = self.hierarchy.get(slug, [])
        return [self.topics[s] for s in child_slugs if s in self.topics]
    
    def get_path(self, slug: str) -> str:
        """Get full path (e.g., 'finance/budget')."""
        topic = self.topics.get(slug)
        if not topic:
            return slug
        
        if not topic.parent_id:
            return slug
        
        # Find parent
        for t in self.topics.values():
            if t.id == topic.parent_id:
                return f"{t.slug}/{slug}"
        
        return slug


# ═══════════════════════════════════════════════════════════════════════════
# Topic Extractor
# ═══════════════════════════════════════════════════════════════════════════

class TopicExtractor:
    """
    Extracts topics from memory items using LLM classification.
    """
    
    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence
        self.topic_tree = TopicTree()
    
    async def load_topics(self, db: AsyncSession) -> None:
        """Load topic tree from database."""
        await self.topic_tree.load_from_db(db)
    
    async def extract(
        self, 
        text: str,
        available_topics: Optional[List[Topic]] = None
    ) -> List[TopicAssignment]:
        """
        Extract topics from text using LLM.
        
        Args:
            text: Text to classify
            available_topics: List of available topics (uses tree if not provided)
            
        Returns:
            List of TopicAssignment with confidence scores
        """
        topics = available_topics or self.topic_tree.get_all()
        
        if not topics:
            return []
        
        # Build prompt
        prompt = self._build_prompt(text, topics)
        
        try:
            # Call LLM (cheap model)
            response = await groq.complete_simple(prompt)
            
            # Parse response
            assignments = self._parse_response(response)
            
            # Validate and filter
            validated = []
            for assignment in assignments:
                if (self.topic_tree.exists(assignment.topic_slug) and 
                    assignment.confidence >= self.min_confidence):
                    topic = self.topic_tree.get(assignment.topic_slug)
                    assignment.topic_id = topic.id if topic else None
                    validated.append(assignment)
            
            return validated
            
        except Exception as e:
            print(f"Error extracting topics: {e}")
            return []
    
    def _build_prompt(self, text: str, topics: List[Topic]) -> str:
        """Build classification prompt."""
        topic_list = []
        for t in topics:
            path = self.topic_tree.get_path(t.slug)
            desc = t.description or t.name
            topic_list.append(f"- {path}: {desc}")
        
        topics_str = "\n".join(topic_list)
        
        return f"""Классифицируй текст по темам. Верни JSON массив.

Доступные темы:
{topics_str}

Текст:
{text[:500]}

Верни JSON массив с темами и confidence (0.0-1.0):
[{{"topic": "slug", "confidence": 0.85}}]

Только JSON, без пояснений. Максимум 3 темы."""
    
    def _parse_response(self, response: str) -> List[TopicAssignment]:
        """Parse LLM response to TopicAssignment list."""
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            data = json.loads(response)
            
            assignments = []
            for item in data:
                if isinstance(item, dict):
                    slug = item.get("topic", "").replace("/", "_").split("/")[-1]
                    confidence = float(item.get("confidence", 0.5))
                    assignments.append(TopicAssignment(
                        topic_slug=slug,
                        confidence=confidence,
                    ))
            
            return assignments
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse topic response: {e}")
            return []


# ═══════════════════════════════════════════════════════════════════════════
# Topic Statistics
# ═══════════════════════════════════════════════════════════════════════════

class TopicStatistics:
    """
    Analytics and statistics for topics.
    """
    
    async def get_activity(
        self, 
        db: AsyncSession,
        topic_id: UUID,
        days: int = 30,
        user_id: Optional[UUID] = None
    ) -> Optional[TopicActivity]:
        """Get activity metrics for a topic."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        sql_text = """
            SELECT 
                t.id as topic_id,
                t.name as topic_name,
                COUNT(mi.id) as item_count,
                COUNT(CASE WHEN mi.item_type = 'decision' THEN 1 END) as decision_count,
                COUNT(CASE WHEN mi.item_type = 'insight' THEN 1 END) as insight_count,
                COALESCE(AVG(mt.confidence), 0) as avg_confidence,
                MAX(mi.created_at) as last_activity
            FROM topics t
            LEFT JOIN memory_topics mt ON t.id = mt.topic_id
            LEFT JOIN memory_items mi ON mt.memory_id = mi.id 
                AND mi.created_at > :cutoff
                AND mi.status = 'active'
        """
        
        params = {"topic_id": topic_id, "cutoff": cutoff}
        
        if user_id:
            sql_text += " AND mi.user_id = :user_id"
            params["user_id"] = user_id
            
        sql_text += " WHERE t.id = :topic_id GROUP BY t.id, t.name"
        
        result = await db.execute(text(sql_text), params)
        row = result.fetchone()
        
        if not row:
            return None
        
        return TopicActivity(
            topic_id=row.topic_id,
            topic_name=row.topic_name,
            item_count=row.item_count or 0,
            decision_count=row.decision_count or 0,
            insight_count=row.insight_count or 0,
            avg_confidence=row.avg_confidence or 0.0,
            last_activity=row.last_activity,
        )
    
    async def get_top_topics(
        self,
        db: AsyncSession,
        days: int = 30,
        limit: int = 10,
        user_id: Optional[UUID] = None
    ) -> List[TopicActivity]:
        """Get most active topics."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        sql_text = """
            SELECT 
                t.id as topic_id,
                t.name as topic_name,
                COUNT(mi.id) as item_count,
                COUNT(CASE WHEN mi.item_type = 'decision' THEN 1 END) as decision_count,
                COUNT(CASE WHEN mi.item_type = 'insight' THEN 1 END) as insight_count,
                COALESCE(AVG(mt.confidence), 0) as avg_confidence,
                MAX(mi.created_at) as last_activity
            FROM topics t
            JOIN memory_topics mt ON t.id = mt.topic_id
            JOIN memory_items mi ON mt.memory_id = mi.id
            WHERE mi.created_at > :cutoff
              AND mi.status = 'active'
        """
        
        params = {"cutoff": cutoff, "limit": limit}
        
        if user_id:
            sql_text += " AND mi.user_id = :user_id"
            params["user_id"] = user_id
            
        sql_text += """
            GROUP BY t.id, t.name
            ORDER BY item_count DESC
            LIMIT :limit
        """
        
        result = await db.execute(text(sql_text), params)
        rows = result.fetchall()
        
        return [
            TopicActivity(
                topic_id=row.topic_id,
                topic_name=row.topic_name,
                item_count=row.item_count,
                decision_count=row.decision_count,
                insight_count=row.insight_count,
                avg_confidence=row.avg_confidence,
                last_activity=row.last_activity,
            )
            for row in rows
        ]
    
    async def get_trends(
        self,
        db: AsyncSession,
        days: int = 30,
        limit: int = 10,
        user_id: Optional[UUID] = None
    ) -> List[TopicTrend]:
        """Get topic trends (rising/falling)."""
        now = datetime.utcnow()
        current_start = now - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)
        
        params = {
            "current_start": current_start,
            "previous_start": previous_start,
            "limit": limit,
        }
        
        user_filter = ""
        if user_id:
            user_filter = " AND mi.user_id = :user_id"
            params["user_id"] = user_id
            
        sql = text(f"""
            WITH current_period AS (
                SELECT mt.topic_id, COUNT(*) as count
                FROM memory_topics mt
                JOIN memory_items mi ON mt.memory_id = mi.id
                WHERE mi.created_at >= :current_start AND mi.status = 'active' {user_filter}
                GROUP BY mt.topic_id
            ),
            previous_period AS (
                SELECT mt.topic_id, COUNT(*) as count
                FROM memory_topics mt
                JOIN memory_items mi ON mt.memory_id = mi.id
                WHERE mi.created_at >= :previous_start 
                  AND mi.created_at < :current_start
                  AND mi.status = 'active' {user_filter}
                GROUP BY mt.topic_id
            )
            SELECT 
                t.id as topic_id,
                t.name as topic_name,
                COALESCE(c.count, 0) as current_count,
                COALESCE(p.count, 0) as previous_count
            FROM topics t
            LEFT JOIN current_period c ON t.id = c.topic_id
            LEFT JOIN previous_period p ON t.id = p.topic_id
            WHERE COALESCE(c.count, 0) > 0 OR COALESCE(p.count, 0) > 0
            ORDER BY COALESCE(c.count, 0) DESC
            LIMIT :limit
        """)
        
        result = await db.execute(sql, params)
        rows = result.fetchall()
        
        trends = []
        for row in rows:
            current = row.current_count or 0
            previous = row.previous_count or 0
            
            if previous > 0:
                change = ((current - previous) / previous) * 100
            elif current > 0:
                change = 100.0
            else:
                change = 0.0
            
            if change > 10:
                trend = "rising"
            elif change < -10:
                trend = "falling"
            else:
                trend = "stable"
            
            trends.append(TopicTrend(
                topic_id=row.topic_id,
                topic_name=row.topic_name,
                current_count=current,
                previous_count=previous,
                change_percent=change,
                trend=trend,
            ))
        
        return trends


# ═══════════════════════════════════════════════════════════════════════════
# Topic Loader
# ═══════════════════════════════════════════════════════════════════════════

class TopicLoader:
    """Loads default topics from YAML config."""
    
    @staticmethod
    def load_from_yaml(filepath: str) -> List[Dict]:
        """Load topics from YAML file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data.get('topics', [])
    
    @staticmethod
    async def seed_topics(db: AsyncSession, filepath: str) -> int:
        """Seed topics from YAML into database."""
        topics_data = TopicLoader.load_from_yaml(filepath)
        count = 0
        
        for topic_data in topics_data:
            count += await TopicLoader._create_topic(db, topic_data, parent_id=None)
        
        await db.commit()
        return count
    
    @staticmethod
    async def _create_topic(
        db: AsyncSession, 
        data: Dict, 
        parent_id: Optional[UUID],
        level: int = 0
    ) -> int:
        """Recursively create topic and children."""
        count = 0
        
        # Check if exists
        result = await db.execute(
            select(Topic).where(Topic.slug == data['slug'])
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            topic = Topic(
                id=uuid4(),
                name=data['name'],
                slug=data['slug'],
                description=data.get('description'),
                keywords=data.get('keywords', []),
                parent_id=parent_id,
                level=level,
                is_system=True,
            )
            db.add(topic)
            count = 1
            topic_id = topic.id
        else:
            topic_id = existing.id
        
        # Create children
        for child in data.get('children', []):
            count += await TopicLoader._create_topic(
                db, child, parent_id=topic_id, level=level + 1
            )
        
        return count


# Global instances
topic_extractor = TopicExtractor()
topic_statistics = TopicStatistics()
