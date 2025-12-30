from fastapi import APIRouter

# Create websockets router
router = APIRouter()

from . import handler
# Include voice router code or add routes directly
router.include_router(handler.router)
