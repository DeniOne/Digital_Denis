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
from core.auth import get_current_user, get_current_user_optional
from memory.models import User


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
    current_user: User = Depends(get_current_user_optional),
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
            user_id=current_user.id,
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


class TelegramMessageRequest(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    content: str
    session_id: Optional[str] = None


@router.post("/telegram", response_model=MessageResponse)
async def send_telegram_message(
    request: TelegramMessageRequest,
    db: AsyncSession = Depends(get_db),
    # Secure this endpoint: Only the bot (possessing the token) can call it.
    # In production, specific IP whitelisting or a shared secret is better.
    # Here we can check a header or simply rely on the fact that this is an internal API.
    # But for safety, let's verify a header potentially.
):
    """
    Handle message explicitly from Telegram Bot.
    Auto-creates user if not exists.
    """
    import os
    from sqlalchemy import select
    from core.config import settings
    
    # ═══════════════════════════════════════════════════════════════════════
    # ACCESS CONTROL - Only whitelisted Telegram IDs can use the system
    # ═══════════════════════════════════════════════════════════════════════
    allowed_ids_str = os.getenv("ALLOWED_TELEGRAM_IDS", "")
    if allowed_ids_str:
        allowed_ids = [int(x.strip()) for x in allowed_ids_str.split(",") if x.strip()]
        if request.telegram_id not in allowed_ids:
            raise HTTPException(
                status_code=403,
                detail="Доступ запрещён. Ваш Telegram ID не в белом списке."
            )
    
    # 1. Find or Create User
    result = await db.execute(select(User).where(User.telegram_id == request.telegram_id))
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(
            telegram_id=request.telegram_id,
            username=request.username,
            full_name=request.full_name,
            role="owner"  # Default role
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # 2. Parse Session
    session_id = None
    if request.session_id:
        try:
            session_id = UUID(request.session_id)
        except ValueError:
            pass
            
    # 3. Process Message
    try:
        response = await request_router.route(
            user_message=request.content,
            session_id=session_id,
            db=db,
            user_id=user.id,
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
async def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_user_optional),
):
    """
    Get chat history for session.
    """
    history = await short_term_memory.get_chat_history(session_id)
    return {"session_id": session_id, "messages": history}
