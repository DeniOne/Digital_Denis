"""
Digital Denis — Topic Auto-Generation API
═══════════════════════════════════════════════════════════════════════════

Endpoints for triggering and managing auto-generated topics.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from uuid import UUID

from db.database import get_db
from analytics.topic_orchestrator import topic_orchestrator
from workers.tasks import run_topic_clustering
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
    # For now, run synchronously or as a Celery task? 
    # Let's use Celery task which returns a result.
    task = run_topic_clustering.delay(str(user_id))
    return {"status": "accepted", "task_id": task.id}

@router.get("/auto-status/{task_id}")
async def get_clustering_status(task_id: str):
    """
    Check the status of a clustering task.
    """
    from celery.result import AsyncResult
    res = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": res.status,
        "result": res.result if res.ready() else None
    }
