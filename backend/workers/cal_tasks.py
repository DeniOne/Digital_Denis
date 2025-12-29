"""
Digital Denis — CAL Celery Tasks
═══════════════════════════════════════════════════════════════════════════

Async background tasks for Cognitive Analytics Layer.
"""

from celery import Celery
from typing import List, Optional
from uuid import UUID


# ═══════════════════════════════════════════════════════════════════════════
# Celery App Configuration
# ═══════════════════════════════════════════════════════════════════════════

app = Celery(
    'cal',
    broker='redis://localhost:6379/1',
    backend='redis://localhost:6379/1'
)

# Configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'workers.cal_tasks.extract_topics': {'queue': 'topics'},
        'workers.cal_tasks.update_graph': {'queue': 'graphs'},
        'workers.cal_tasks.analyze_decision': {'queue': 'analytics'},
        'workers.cal_tasks.detect_anomalies': {'queue': 'analytics'},
    },
)


# ═══════════════════════════════════════════════════════════════════════════
# Topic Extraction Tasks
# ═══════════════════════════════════════════════════════════════════════════

@app.task(queue='topics', bind=True, max_retries=3)
def extract_topics(self, memory_item_id: str):
    """
    Extract and assign topics to a memory item.
    Triggered when new memory is created.
    """
    import asyncio
    from db.database import async_session_maker
    from analytics.topics import topic_extractor
    from memory.models import MemoryItem, MemoryTopic
    from sqlalchemy import select
    from uuid import UUID as PyUUID
    
    async def _extract():
        async with async_session_maker() as db:
            # Get memory item
            result = await db.execute(
                select(MemoryItem).where(MemoryItem.id == PyUUID(memory_item_id))
            )
            item = result.scalar_one_or_none()
            
            if not item:
                return {"status": "not_found"}
            
            # Load topic tree
            await topic_extractor.load_topics(db)
            
            # Extract topics
            topics = await topic_extractor.extract(item.content)
            
            # Save assignments
            for topic in topics:
                if topic.topic_id:
                    mt = MemoryTopic(
                        memory_id=item.id,
                        topic_id=topic.topic_id,
                        confidence=topic.confidence,
                        assigned_by="cal",
                    )
                    db.add(mt)
            
            await db.commit()
            return {"status": "ok", "topics_count": len(topics)}
    
    try:
        return asyncio.run(_extract())
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@app.task(queue='topics')
def update_topic_stats(topic_ids: List[str]):
    """Update daily statistics for topics."""
    import asyncio
    from db.database import async_session_maker
    from analytics.cal_models import CALTopicStats
    from datetime import date
    from uuid import UUID as PyUUID, uuid4
    from sqlalchemy import select, and_
    
    async def _update():
        async with async_session_maker() as db:
            today = date.today()
            
            for topic_id_str in topic_ids:
                topic_id = PyUUID(topic_id_str)
                
                # Check if exists
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
            
            await db.commit()
            return {"status": "ok", "topics_updated": len(topic_ids)}
    
    return asyncio.run(_update())


# ═══════════════════════════════════════════════════════════════════════════
# Graph Update Tasks
# ═══════════════════════════════════════════════════════════════════════════

@app.task(queue='graphs', bind=True, max_retries=3)
def update_graph(self, memory_item_ids: List[str]):
    """
    Update mind map graph with new items.
    Creates nodes and finds connections.
    """
    import asyncio
    from db.database import async_session_maker
    from analytics.cal_service import cal_service
    from analytics.cal_models import CALGraphNode
    from memory.models import MemoryItem
    from sqlalchemy import select
    from uuid import UUID as PyUUID
    
    async def _update():
        async with async_session_maker() as db:
            nodes_created = 0
            edges_created = 0
            
            for item_id_str in memory_item_ids:
                item_id = PyUUID(item_id_str)
                
                # Get memory item
                result = await db.execute(
                    select(MemoryItem).where(MemoryItem.id == item_id)
                )
                item = result.scalar_one_or_none()
                
                if not item:
                    continue
                
                # Check if node exists
                node_result = await db.execute(
                    select(CALGraphNode).where(CALGraphNode.memory_id == item_id)
                )
                node = node_result.scalar_one_or_none()
                
                if not node:
                    node = await cal_service._create_graph_node(db, item)
                    nodes_created += 1
                
                # Find connections
                edges = await cal_service.find_connections(db, node.id)
                edges_created += len(edges)
            
            await db.commit()
            return {
                "status": "ok",
                "nodes_created": nodes_created,
                "edges_created": edges_created,
            }
    
    try:
        return asyncio.run(_update())
    except Exception as exc:
        self.retry(exc=exc, countdown=120)


@app.task(queue='graphs')
def update_graph_batch():
    """
    Batch update: process recent ungraphed items.
    Runs periodically.
    """
    import asyncio
    from db.database import async_session_maker
    from analytics.cal_models import CALGraphNode
    from memory.models import MemoryItem
    from sqlalchemy import select, and_
    from datetime import datetime, timedelta
    
    async def _batch():
        async with async_session_maker() as db:
            # Find items without nodes (last hour)
            cutoff = datetime.utcnow() - timedelta(hours=1)
            
            # Get recent memory items
            result = await db.execute(
                select(MemoryItem.id)
                .where(
                    and_(
                        MemoryItem.created_at > cutoff,
                        MemoryItem.status == "active"
                    )
                )
                .limit(100)
            )
            item_ids = [str(r[0]) for r in result.fetchall()]
            
            if item_ids:
                # Trigger individual updates
                update_graph.delay(item_ids)
            
            return {"status": "ok", "queued_items": len(item_ids)}
    
    return asyncio.run(_batch())


# ═══════════════════════════════════════════════════════════════════════════
# Decision Analysis Tasks
# ═══════════════════════════════════════════════════════════════════════════

@app.task(queue='analytics', bind=True, max_retries=3)
def analyze_decision(self, decision_id: str):
    """
    Analyze decision quality and risks.
    Triggered when new decision is saved.
    """
    import asyncio
    from db.database import async_session_maker
    from analytics.cal_service import cal_service
    from uuid import UUID as PyUUID
    
    async def _analyze():
        async with async_session_maker() as db:
            result = await cal_service.analyze_decision(db, PyUUID(decision_id))
            await db.commit()
            
            if result:
                return {
                    "status": "ok",
                    "overall_score": result.overall_score,
                    "risk_level": result.risk_level,
                }
            return {"status": "not_found"}
    
    try:
        return asyncio.run(_analyze())
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


# ═══════════════════════════════════════════════════════════════════════════
# Anomaly Detection Tasks
# ═══════════════════════════════════════════════════════════════════════════

@app.task(queue='analytics')
def detect_anomalies():
    """
    Periodic anomaly detection.
    Compares current metrics with baseline.
    """
    import asyncio
    from db.database import async_session_maker
    from analytics.cal_service import cal_service
    
    async def _detect():
        async with async_session_maker() as db:
            anomalies = await cal_service.detect_anomalies(db)
            await db.commit()
            
            return {
                "status": "ok",
                "anomalies_detected": len(anomalies),
            }
    
    return asyncio.run(_detect())


@app.task(queue='analytics')
def create_health_snapshot():
    """
    Create daily cognitive health snapshot.
    Runs once per day.
    """
    import asyncio
    from db.database import async_session_maker
    from analytics.cal_service import cal_service
    
    async def _snapshot():
        async with async_session_maker() as db:
            snapshot = await cal_service.create_health_snapshot(db)
            return {
                "status": "ok",
                "overall_score": snapshot.overall_health_score,
            }
    
    return asyncio.run(_snapshot())


# ═══════════════════════════════════════════════════════════════════════════
# Celery Beat Schedule
# ═══════════════════════════════════════════════════════════════════════════

app.conf.beat_schedule = {
    'detect-anomalies-hourly': {
        'task': 'workers.cal_tasks.detect_anomalies',
        'schedule': 3600.0,  # Every hour
    },
    'update-graph-batch': {
        'task': 'workers.cal_tasks.update_graph_batch',
        'schedule': 300.0,  # Every 5 minutes
    },
    'health-snapshot-daily': {
        'task': 'workers.cal_tasks.create_health_snapshot',
        'schedule': 86400.0,  # Daily
    },
}
