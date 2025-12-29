"""
Digital Denis — Messages API Routes
═══════════════════════════════════════════════════════════════════════════

API endpoints for message handling.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db.database import get_db, AsyncSession
from orchestrator.router import router as request_router
from memory.short_term import short_term_memory


router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════

class MessageRequest(BaseModel):
    content: str
    session_id: Optional[str] = None


class MessageResponse(BaseModel):
    response: str
    agent: str
    session_id: str
    memory_saved: bool = False
    tokens_used: int = 0


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.post("", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send message to Digital Denis.
    
    Returns agent response with metadata.
    """
    # Parse session ID
    session_id = None
    if request.session_id:
        try:
            session_id = UUID(request.session_id)
        except ValueError:
            pass
    
    # Route to appropriate agent
    try:
        response = await request_router.route(
            user_message=request.content,
            session_id=session_id,
            db=db,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return MessageResponse(
        response=response.content,
        agent=response.agent,
        session_id=str(response.follow_up) if response.follow_up else str(session_id or ""),
        memory_saved=response.save_to_memory,
        tokens_used=response.tokens_used,
    )


@router.get("/session/{session_id}")
async def get_session_history(session_id: str):
    """
    Get chat history for session.
    """
    history = await short_term_memory.get_chat_history(session_id)
    return {"session_id": session_id, "messages": history}
