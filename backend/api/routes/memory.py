"""
Digital Denis — Memory API Routes
═══════════════════════════════════════════════════════════════════════════

API endpoints for memory operations.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from db.database import get_db, AsyncSession
from memory.long_term import long_term_memory
from core.auth import get_current_user_optional
from memory.models import User


router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════

class MemoryItemResponse(BaseModel):
    id: str
    item_type: str
    content: str
    summary: Optional[str] = None
    confidence: float = 0.5
    status: str = "active"
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class MemoryListResponse(BaseModel):
    items: List[MemoryItemResponse]
    total: int


class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 10


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("", response_model=MemoryListResponse)
async def list_memories(
    item_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """
    List memory items with optional filters.
    """
    items = await long_term_memory.list(
        db=db,
        user_id=current_user.id,
        item_type=item_type,
        limit=limit,
        offset=offset,
    )
    
    return MemoryListResponse(
        items=[
            MemoryItemResponse(
                id=str(item.id),
                item_type=item.item_type,
                content=item.content,
                summary=item.summary,
                confidence=item.confidence,
                status=item.status,
                created_at=item.created_at.isoformat() if item.created_at else None,
            )
            for item in items
        ],
        total=len(items),  # TODO: proper count query
    )


@router.get("/{item_id}", response_model=MemoryItemResponse)
async def get_memory(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """
    Get single memory item by ID.
    """
    try:
        uuid_id = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
    
    item = await long_term_memory.get(db, uuid_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Memory item not found")
    
    return MemoryItemResponse(
        id=str(item.id),
        item_type=item.item_type,
        content=item.content,
        summary=item.summary,
        confidence=item.confidence,
        status=item.status,
        created_at=item.created_at.isoformat() if item.created_at else None,
    )


@router.post("/search")
async def search_memories(
    request: MemorySearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """
    Search memories by text query.
    """
    items = await long_term_memory.search(
        db=db,
        user_id=current_user.id,
        query_text=request.query,
        limit=request.limit,
    )
    
    return {
        "query": request.query,
        "results": [
            {
                "id": str(item.id),
                "item_type": item.item_type,
                "content": item.content[:200],
                "summary": item.summary,
            }
            for item in items
        ],
    }


@router.delete("/{item_id}")
async def delete_memory(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """
    Soft delete memory item.
    """
    try:
        uuid_id = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
    
    item = await long_term_memory.get(db, uuid_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Memory item not found")
    
    success = await long_term_memory.delete(db, uuid_id)
    
    return {"status": "deleted", "id": item_id}
