import json
from datetime import datetime, time
import logging
from typing import Optional

from pywebpush import webpush, WebPushException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.config import settings
from memory.models import PushSubscription
from memory.models import User
# Assuming we have a redis client or similar for rate limiting, but for now we'll keep it simple
# from core.redis import redis_client

logger = logging.getLogger(__name__)

def is_quiet_hours(user_settings: dict) -> bool:
    """Check if current time is within quiet hours."""
    if not user_settings:
        return False
        
    start_str = user_settings.get("quiet_hours_start")
    end_str = user_settings.get("quiet_hours_end")
    
    if not start_str or not end_str:
        return False
        
    try:
        now = datetime.now().time()
        start = datetime.strptime(start_str, "%H:%M").time()
        end = datetime.strptime(end_str, "%H:%M").time()
        
        if start < end:
            return start <= now <= end
        else: # Crosses midnight
            return now >= start or now <= end
    except ValueError:
        logger.error(f"Invalid time format in settings: {start_str}, {end_str}")
        return False

async def send_push_notification(subscription_info: dict, title: str, body: str, data: dict = None, user_settings: dict = None):
    """
    Send a push notification to a specific subscription with business logic checks.
    """
    # 1. Quiet Hours Check
    if user_settings and is_quiet_hours(user_settings):
        # Allow 'urgent' notifications to bypass
        if data and data.get('priority') == 'high':
            pass
        else:
            logger.info("Notification suppressed due to quiet hours.")
            return False

    # 2. Rate Limiting
    # key = f"rate_limit:push:{subscription_info['endpoint']}"
    # count = await redis_client.incr(key)
    # if count > 10: return False
    from memory.short_term import short_term_memory
    
    # We limit by Endpoint to avoid spamming a single device too much
    # Limit: 10 per hour
    try:
        redis = short_term_memory.redis
        if redis:
            key = f"rate_limit:push:{subscription_info['endpoint']}"
            current_count = await redis.incr(key)
            if current_count == 1:
                await redis.expire(key, 3600)  # 1 hour window
            
            if current_count > 10:
                logger.warning(f"Rate limit exceeded for {subscription_info['endpoint'][:20]}")
                return False
    except Exception as e:
        logger.warning(f"Rate limit check failed: {e}")
        # Fail open (allow notification) if Redis is down
        pass
    
    try:
        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": "/icons/pwa/icon-192x192.png",
            "data": data or {}
        })
        
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={
                "sub": settings.vapid_claims_sub
            }
        )
        logger.info(f"Push notification sent to {subscription_info.get('endpoint')[:20]}...")
        return True
        
    except WebPushException as ex:
        logger.error(f"WebPush failed: {repr(ex)}")
        if ex.response and ex.response.status_code == 410:
             return False 
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending push: {e}")
        return False

async def send_notification_to_user(user_id: str, title: str, body: str, data: dict = None, db: AsyncSession = None):
    """
    High-level helper to send to all user devices.
    """
    if not db:
        logger.error("DB session required for sending to user")
        return 0

    # Get User & Settings
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        return 0
        
    user_settings = user.notification_settings or {}
    
    # Get Subscriptions
    result = await db.execute(select(PushSubscription).filter_by(user_id=user_id))
    subs = result.scalars().all()
    
    sent_count = 0
    for sub in subs:
        sub_info = {"endpoint": sub.endpoint, "keys": sub.keys}
        success = await send_push_notification(sub_info, title, body, data, user_settings)
        if success:
            sent_count += 1
            
    return sent_count
