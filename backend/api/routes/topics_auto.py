"""
Digital Den — Topic Auto-Generation API
═══════════════════════════════════════════════════════════════════════════

Endpoints for triggering and managing auto-generated topics.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from uuid import UUID

from db.database import get_db
from analytics.topic_orchestrator import topic_orchestrator
# Celery imports are lazy to allow server startup without celery installed
# from api.auth import get_current_user # Assuming auth exist

router = APIRouter(prefix="/topics", tags=["topics"])

@router.post("/auto-generate")
async def trigger_auto_clustering(
    user_id: UUID,  # Should be from auth in real app
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger unsupervised clustering of memories for the given user.
    """
    try:
        from workers.tasks import run_topic_clustering
        task = run_topic_clustering.delay(str(user_id))
        return {"status": "accepted", "task_id": task.id}
    except ImportError:
        # Celery not available - run synchronously
        result = await topic_orchestrator.run_auto_clustering(db, user_id)
        return {"status": "completed", "result": result}

@router.get("/auto-status/{task_id}")
async def get_clustering_status(task_id: str):
    """
    Check the status of a clustering task.
    """
    try:
        from celery.result import AsyncResult
        res = AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": res.status,
            "result": res.result if res.ready() else None
        }
    except ImportError:
        return {
            "task_id": task_id,
            "status": "unavailable",
            "error": "Celery not installed"
        }
