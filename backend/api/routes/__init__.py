"""
Digital Denis — API Routes
═══════════════════════════════════════════════════════════════════════════

Unified API router combining all endpoints.
"""

from fastapi import APIRouter

# Import all route modules
from api.routes import messages
from api.routes import memory
from api.routes import topics
from api.routes import mindmap
from api.routes import cal
from api.routes import decisions
from api.routes import anomalies
from api.routes import health
from api.routes import tts
from api.routes import auth
from api.routes import notifications
from api.routes import topics_auto
from api.routes import analytics


# Create main router
api_router = APIRouter(prefix="/api/v1")


# Include all sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(messages.router, prefix="/messages", tags=["Messages"])
api_router.include_router(memory.router, prefix="/memory", tags=["Memory"])
api_router.include_router(topics.router, prefix="/topics", tags=["Topics List"])
api_router.include_router(topics_auto.router, tags=["Topic Clustering"])
api_router.include_router(mindmap.router, prefix="/mindmap", tags=["Mind Map"])
api_router.include_router(cal.router, prefix="/cal", tags=["CAL"])
api_router.include_router(decisions.router, prefix="/decisions", tags=["Decisions"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["Anomalies"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(tts.router, prefix="/voice", tags=["Voice"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(analytics.router, tags=["Analytics"])

# WebSockets
from api.websockets import handler as voice_ws
api_router.include_router(voice_ws.router, tags=["Voice"])


# Export for main app
__all__ = ["api_router"]
