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


# Create main router
api_router = APIRouter(prefix="/api/v1")


# Include all sub-routers
api_router.include_router(messages.router, tags=["Messages"])
api_router.include_router(memory.router, tags=["Memory"])
api_router.include_router(topics.router, tags=["Topics"])
api_router.include_router(mindmap.router, tags=["Mind Map"])
api_router.include_router(cal.router, tags=["CAL"])
api_router.include_router(decisions.router, tags=["Decisions"])
api_router.include_router(anomalies.router, tags=["Anomalies"])
api_router.include_router(health.router, tags=["Health"])


# Export for main app
__all__ = ["api_router"]
