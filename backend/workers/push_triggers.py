import logging
from db.database import async_session
from core.notifications import send_notification_to_user

logger = logging.getLogger(__name__)

async def check_daily_digest():
    """
    Scheduled task to send daily digest.
    Should be called by Celery or a scheduler.
    """
    async with async_session() as db:
        # TODO: Iterate over users with 'daily_digest' enabled
        # For now, just a stub
        pass

async def check_incomplete_tasks():
    """
    Scheduled task to remind about incomplete tasks.
    """
    async with async_session() as db:
        # TODO: Check tasks logic
        pass

async def send_agent_insight(user_id: str, insight_text: str):
    """
    Triggered by Agent when a new important insight is generated.
    """
    async with async_session() as db:
        await send_notification_to_user(
            user_id=user_id,
            title="✨ Новый инсайт",
            body=insight_text,
            data={"type": "insight"},
            db=db
        )
