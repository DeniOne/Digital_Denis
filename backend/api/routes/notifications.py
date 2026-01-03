from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from db.database import get_db
from memory.models import PushSubscription, User
from core.auth import get_current_user
from pydantic import BaseModel
from core.notifications import send_push_notification
from core.config import settings

router = APIRouter()

class PushSubscriptionCreate(BaseModel):
    endpoint: str
    keys: dict

@router.get("/vapid-public-key")
async def get_vapid_key(current_user: User = Depends(get_current_user)):
    return {"public_key": settings.vapid_public_key}

@router.post("/subscribe")
async def subscribe(
    subscription: PushSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if exists
    result = await db.execute(select(PushSubscription).filter_by(endpoint=subscription.endpoint, user_id=current_user.id))
    existing = result.scalars().first()
    
    if existing:
        return {"status": "already_subscribed"}
    
    new_sub = PushSubscription(
        user_id=current_user.id,
        endpoint=subscription.endpoint,
        keys=subscription.keys
    )
    db.add(new_sub)
    await db.commit()
    
    # Send welcome push
    await send_push_notification(
        subscription.model_dump(),
        "Digital Den",
        "Уведомления успешно подключены!",
        {"type": "welcome"}
    )
    
    return {"status": "subscribed"}

@router.delete("/unsubscribe")
async def unsubscribe(
    endpoint: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(PushSubscription).filter_by(endpoint=endpoint, user_id=current_user.id))
    sub = result.scalars().first()
    
    if sub:
        await db.delete(sub)
        await db.commit()
        
    return {"status": "unsubscribed"}

@router.post("/test")
async def test_push(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get user subscriptions
    result = await db.execute(select(PushSubscription).filter_by(user_id=current_user.id))
    subs = result.scalars().all()
    
    count = 0
    for sub in subs:
        sub_info = {"endpoint": sub.endpoint, "keys": sub.keys}
        success = await send_push_notification(sub_info, "Test Push", "This is a test notification from Digital Den.")
        if success:
            count += 1
            
    return {"sent_count": count}
