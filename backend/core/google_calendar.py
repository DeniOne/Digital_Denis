"""
Digital Denis — Google Calendar Service
═══════════════════════════════════════════════════════════════════════════

Service for interacting with Google Calendar API and syncing items.
"""

import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from memory.google_auth_models import GoogleAuthToken, GoogleCalendarConfig
from memory.schedule_models import ScheduleItem, ItemType, ItemStatus
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class GoogleCalendarService:
    """
    Manages synchronization between Digital Denis Schedule and Google Calendar.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_credentials(self, user_id: Any) -> Optional[Credentials]:
        """Load Google credentials for a user."""
        result = await self.db.execute(
            select(GoogleAuthToken).where(GoogleAuthToken.user_id == user_id)
        )
        token = result.scalars().first()
        
        if not token:
            return None
            
        credentials = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=token.scopes
        )
        
        # Check if expired and refresh if needed
        if token.expires_at < datetime.utcnow():
            from google.auth.transport.requests import Request as GoogleRequest
            try:
                credentials.refresh(GoogleRequest())
                token.access_token = credentials.token
                token.expires_at = credentials.expiry
                await self.db.commit()
            except Exception as e:
                logger.error("google_token_refresh_error", user_id=str(user_id), error=str(e))
                return None
                
        return credentials

    async def create_event(self, item: ScheduleItem) -> Optional[str]:
        """
        Create an event in Google Calendar from a ScheduleItem.
        Returns the Google Event ID.
        """
        creds = await self._get_credentials(item.user_id)
        if not creds:
            return None
            
        try:
            service = build('calendar', 'v3', credentials=creds)
            
            event_body = {
                'summary': item.title,
                'description': item.description or "",
                'start': {
                    'dateTime': item.start_at.isoformat() if item.start_at else datetime.now(timezone.utc).isoformat(),
                    'timeZone': item.timezone,
                },
                'end': {
                    'dateTime': item.end_at.isoformat() if item.end_at else (item.start_at + timedelta(hours=1)).isoformat(),
                    'timeZone': item.timezone,
                },
                'extendedProperties': {
                    'private': {
                        'dd_id': str(item.id),
                        'source': 'digital_denis'
                    }
                }
            }
            
            event = service.events().insert(calendarId='primary', body=event_body).execute()
            logger.info("google_event_created", item_id=str(item.id), google_id=event.get('id'))
            return event.get('id')
            
        except HttpError as error:
            logger.error("google_api_error", action="create_event", error=str(error))
            return None
        except Exception as e:
            logger.error("google_service_error", action="create_event", error=str(e))
            return None

    async def sync_to_google(self, user_id: Any):
        """
        Push all pending/unsynced local items to Google Calendar.
        """
        result = await self.db.execute(
            select(ScheduleItem).where(
                ScheduleItem.user_id == user_id,
                ScheduleItem.google_event_id == None,
                ScheduleItem.item_type == ItemType.EVENT
            )
        )
        items = result.scalars().all()
        
        for item in items:
            google_id = await self.create_event(item)
            if google_id:
                item.google_event_id = google_id
        
        await self.db.commit()

    async def sync_from_google(self, user_id: Any):
        """
        Fetch changes from Google Calendar and update local Schedule.
        (Implementation would use sync tokens and list events)
        """
        # Placeholder for basic listing
        creds = await self._get_credentials(user_id)
        if not creds:
            return
            
        try:
            service = build('calendar', 'v3', credentials=creds)
            now = datetime.utcnow().isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary', timeMin=now,
                maxResults=10, singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            
            # TODO: Match events by dd_id in extendedProperties or by title/time
            logger.info("google_sync_from", count=len(events))
            
        except Exception as e:
            logger.error("google_sync_from_error", error=str(e))

from datetime import timedelta # Needed for end_at calculation
