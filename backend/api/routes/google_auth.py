"""
Digital Den — Google Auth Routes
═══════════════════════════════════════════════════════════════════════════

API endpoints for Google OAuth2 authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials

from db.database import get_db
from core.config import settings
from memory.models import User
from memory.google_auth_models import GoogleAuthToken, GoogleCalendarConfig
from api.routes.auth import get_current_user_optional
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth/google", tags=["google-auth"])

# Scopes required for Calendar access
SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]


@router.get("")
async def authorize_google(
    user_id: str = None, # Optional if not logged in via main auth yet
    db: AsyncSession = Depends(get_db)
):
    """
    Step 1: Get the authorization URL.
    """
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth not configured on server")

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES
    )

    flow.redirect_uri = settings.google_redirect_uri

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent' # Force refresh token
    )

    # In a real app, we should save 'state' in session/redis to verify in callback
    return {"url": authorization_url}


@router.get("/callback")
async def google_callback(
    request: Request,
    code: str,
    state: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2: Exchange code for tokens and save them.
    """
    # Hardcoded for now, in multi-user this comes from 'state' or session
    # For Denis, there is usually only one primary user
    result = await db.execute(select(User).where(User.role == "owner"))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Owner user not found")

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = settings.google_redirect_uri

    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Save or update token
        token_result = await db.execute(select(GoogleAuthToken).where(GoogleAuthToken.user_id == user.id))
        token_entry = token_result.scalars().first()
        
        if not token_entry:
            token_entry = GoogleAuthToken(user_id=user.id)
            db.add(token_entry)
            
        token_entry.access_token = credentials.token
        if credentials.refresh_token:
            token_entry.refresh_token = credentials.refresh_token
        
        token_entry.expires_at = datetime.utcnow() + timedelta(seconds=credentials.expiry.timestamp() - datetime.now().timestamp() if credentials.expiry else 3600)
        token_entry.scopes = credentials.scopes
        
        # Also ensure Calendar Config exists
        config_result = await db.execute(select(GoogleCalendarConfig).where(GoogleCalendarConfig.user_id == user.id))
        config_entry = config_result.scalars().first()
        if not config_entry:
            config_entry = GoogleCalendarConfig(user_id=user.id)
            db.add(config_entry)

        await db.commit()
        
        logger.info("google_auth_success", user_id=str(user.id))
        
        # Redirect back to frontend
        return RedirectResponse(url="http://localhost:3000/settings?google=success")
        
    except Exception as e:
        logger.error("google_auth_error", error=str(e))
        await db.rollback()
        return RedirectResponse(url="http://localhost:3000/settings?google=error")


@router.get("/status")
async def get_google_status(
    db: AsyncSession = Depends(get_db)
):
    """Check if Google integration is active."""
    result = await db.execute(select(User).where(User.role == "owner"))
    user = result.scalars().first()
    
    if not user:
        return {"active": False}
        
    token_result = await db.execute(select(GoogleAuthToken).where(GoogleAuthToken.user_id == user.id))
    token = token_result.scalars().first()
    
    return {
        "active": token is not None,
        "email": token.google_email if token else None,
        "expires_at": token.expires_at if token else None
    }


@router.post("/sync")
async def trigger_google_sync(
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger Google Calendar sync for owner."""
    from core.google_calendar import GoogleCalendarService
    
    result = await db.execute(select(User).where(User.role == "owner"))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Owner not found")
        
    service = GoogleCalendarService(db)
    try:
        await service.sync_to_google(user.id)
        await service.sync_from_google(user.id)
        return {"status": "ok", "message": "Synchronization triggered"}
    except Exception as e:
        logger.error("manual_google_sync_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
