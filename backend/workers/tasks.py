"""
Digital Denis — Main Celery Tasks
═══════════════════════════════════════════════════════════════════════════

Core background tasks for Digital Denis system.
Includes: embeddings, memory aggregation, maintenance.
"""

import asyncio
from celery import Celery
from celery.schedules import crontab
from typing import List, Optional
from datetime import datetime, timedelta


# ═══════════════════════════════════════════════════════════════════════════
# Celery App Configuration
# ═══════════════════════════════════════════════════════════════════════════

app = Celery(
    'digital_denis',
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
    
    # Queue routing
    task_routes={
        'workers.tasks.extract_topics': {'queue': 'topics'},
        'workers.tasks.update_embeddings': {'queue': 'embeddings'},
        'workers.tasks.analyze_decision': {'queue': 'analytics'},
        'workers.tasks.update_graph_batch': {'queue': 'graphs'},
        'workers.tasks.detect_anomalies': {'queue': 'analytics'},
        'workers.tasks.aggregate_memory': {'queue': 'memory'},
        'workers.tasks.cleanup_sessions': {'queue': 'maintenance'},
        'workers.tasks.cleanup_old_data': {'queue': 'maintenance'},
    },
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # Result expiration
    result_expires=3600,
)


# ═══════════════════════════════════════════════════════════════════════════
# Embeddings Tasks
# ═══════════════════════════════════════════════════════════════════════════

@app.task(queue='embeddings', bind=True, max_retries=3)
def update_embeddings(self, memory_id: str):
    """
    Update vector embeddings for a memory item.
    High priority - triggered on new/updated item.
    """
    from db.database import async_session_maker
    from memory.semantic import semantic_memory
    from memory.models import MemoryItem
    from sqlalchemy import select
    from uuid import UUID
    
    async def _update():
        async with async_session_maker() as db:
            result = await db.execute(
                select(MemoryItem).where(MemoryItem.id == UUID(memory_id))
            )
            item = result.scalar_one_or_none()
            
            if not item:
                return {"status": "not_found"}
            
            # Index in semantic memory
            await semantic_memory.index(db, item)
            
            return {"status": "ok", "memory_id": memory_id}
    
    try:
        return asyncio.run(_update())
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@app.task(queue='embeddings')
def reindex_all_embeddings(limit: int = 100):
    """
    Reindex all memory embeddings.
    Used for vector DB migration or model updates.
    """
    from db.database import async_session_maker
    from memory.semantic import semantic_memory
    from memory.models import MemoryItem
    from sqlalchemy import select
    
    async def _reindex():
        async with async_session_maker() as db:
            result = await db.execute(
                select(MemoryItem)
                .where(MemoryItem.status == "active")
                .limit(limit)
            )
            items = result.scalars().all()
            
            indexed = 0
            for item in items:
                try:
                    await semantic_memory.index(db, item)
                    indexed += 1
                except Exception:
                    pass
            
            return {"status": "ok", "indexed": indexed, "total": len(items)}
    
    return asyncio.run(_reindex())


# ═══════════════════════════════════════════════════════════════════════════
# Memory Aggregation Tasks
# ═══════════════════════════════════════════════════════════════════════════

@app.task(queue='memory')
def aggregate_memory():
    """
    Daily memory aggregation.
    Clusters similar memories and creates summary items.
    Runs at 2am.
    """
    from db.database import async_session_maker
    from agents.memory_agent import memory_agent_v2
    
    async def _aggregate():
        async with async_session_maker() as db:
            clusters = await memory_agent_v2.aggregate_similar(db)
            await db.commit()
            
            return {
                "status": "ok",
                "clusters_created": len(clusters),
            }
    
    return asyncio.run(_aggregate())


@app.task(queue='memory')
def archive_old_memories(days_old: int = 365):
    """
    Archive memories older than specified days.
    Moves to archive status for long-term storage.
    """
    from db.database import async_session_maker
    from memory.models import MemoryItem
    from sqlalchemy import select, update, and_
    
    async def _archive():
        async with async_session_maker() as db:
            cutoff = datetime.utcnow() - timedelta(days=days_old)
            
            result = await db.execute(
                update(MemoryItem)
                .where(
                    and_(
                        MemoryItem.created_at < cutoff,
                        MemoryItem.status == "active"
                    )
                )
                .values(status="archived")
                .returning(MemoryItem.id)
            )
            archived = len(result.fetchall())
            await db.commit()
            
            return {"status": "ok", "archived": archived}
    
    return asyncio.run(_archive())


# ═══════════════════════════════════════════════════════════════════════════
# Session Cleanup Tasks
# ═══════════════════════════════════════════════════════════════════════════

@app.task(queue='maintenance')
def cleanup_sessions():
    """
    Clean up old/expired sessions.
    Hourly task.
    """
    from db.database import async_session_maker
    from memory.models import Session
    from sqlalchemy import select, update, and_
    
    async def _cleanup():
        async with async_session_maker() as db:
            # End sessions inactive for more than 2 hours
            cutoff = datetime.utcnow() - timedelta(hours=2)
            
            result = await db.execute(
                update(Session)
                .where(
                    and_(
                        Session.ended_at.is_(None),
                        Session.started_at < cutoff
                    )
                )
                .values(ended_at=datetime.utcnow())
                .returning(Session.id)
            )
            cleaned = len(result.fetchall())
            await db.commit()
            
            return {"status": "ok", "sessions_closed": cleaned}
    
    return asyncio.run(_cleanup())


@app.task(queue='maintenance')
def cleanup_old_data():
    """
    Clean up old temporary data.
    Weekly maintenance task.
    """
    from db.database import async_session_maker
    from memory.models import Session, Message
    from sqlalchemy import select, delete, and_
    
    async def _cleanup():
        async with async_session_maker() as db:
            # Delete sessions older than 90 days
            cutoff = datetime.utcnow() - timedelta(days=90)
            
            # First delete messages
            msg_result = await db.execute(
                delete(Message)
                .where(
                    Message.session_id.in_(
                        select(Session.id).where(Session.started_at < cutoff)
                    )
                )
                .returning(Message.id)
            )
            deleted_msgs = len(msg_result.fetchall())
            
            # Then delete sessions
            session_result = await db.execute(
                delete(Session)
                .where(Session.started_at < cutoff)
                .returning(Session.id)
            )
            deleted_sessions = len(session_result.fetchall())
            
            await db.commit()
            
            return {
                "status": "ok",
                "deleted_sessions": deleted_sessions,
                "deleted_messages": deleted_msgs,
            }
    
    return asyncio.run(_cleanup())


# ═══════════════════════════════════════════════════════════════════════════
# Health & Monitoring Tasks
# ═══════════════════════════════════════════════════════════════════════════

@app.task(queue='maintenance')
def system_health_check():
    """
    System health check.
    Verifies all components are working.
    """
    from db.database import async_session_maker
    from sqlalchemy import select, func
    
    async def _check():
        results = {}
        
        # Check database
        try:
            async with async_session_maker() as db:
                await db.execute(select(func.now()))
            results["database"] = "ok"
        except Exception as e:
            results["database"] = f"error: {str(e)}"
        
        # Check Redis
        try:
            import redis
            r = redis.from_url("redis://localhost:6379/0")
            r.ping()
            results["redis"] = "ok"
        except Exception as e:
            results["redis"] = f"error: {str(e)}"
        
        results["timestamp"] = datetime.utcnow().isoformat()
        return results
    
    return asyncio.run(_check())


# ═══════════════════════════════════════════════════════════════════════════
# Celery Beat Schedule
# ═══════════════════════════════════════════════════════════════════════════

app.conf.beat_schedule = {
    # CAL tasks
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
        'schedule': crontab(hour=0, minute=0),  # Midnight
    },
    
    # Memory tasks
    'aggregate-memory-daily': {
        'task': 'workers.tasks.aggregate_memory',
        'schedule': crontab(hour=2, minute=0),  # 2am daily
    },
    
    # Maintenance tasks
    'cleanup-sessions-hourly': {
        'task': 'workers.tasks.cleanup_sessions',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-old-data-weekly': {
        'task': 'workers.tasks.cleanup_old_data',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3am
    },
    'health-check-every-5min': {
        'task': 'workers.tasks.system_health_check',
        'schedule': 300.0,  # Every 5 minutes
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# Task Hooks
# ═══════════════════════════════════════════════════════════════════════════

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing."""
    return f"Request: {self.request!r}"
