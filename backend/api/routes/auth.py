"""
Digital Den — Authentication API Routes
═══════════════════════════════════════════════════════════════════════════

Endpoints for user authentication and profile management.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from core.config import settings
from core.auth import create_access_token, verify_telegram_data, get_current_user, get_current_user_optional
from memory.models import User

router = APIRouter()


@router.post("/telegram")
async def telegram_auth(
    auth_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user via Telegram Login Widget data.
    """
    # 1. Verify Telegram data
    if not settings.telegram_bot_token:
        raise HTTPException(
            status_code=500,
            detail="Telegram bot token not configured"
        )
    
    if not verify_telegram_data(auth_data, settings.telegram_bot_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication data"
        )
    
    # 2. Find or create user
    tg_id = int(auth_data.get("id"))
    username = auth_data.get("username")
    first_name = auth_data.get("first_name", "")
    last_name = auth_data.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip()
    
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(
            telegram_id=tg_id,
            username=username,
            full_name=full_name,
            role="owner"  # Default to owner for MVP
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update existing user data
        user.username = username
        user.full_name = full_name
        await db.commit()
    
    # 3. Create access token
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role
        }
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user_optional)):
    """
    Get current user profile.
    """
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "created_at": current_user.created_at
    }
