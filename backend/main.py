"""
Digital Denis — Backend API
═══════════════════════════════════════════════════════════════════════════

Personal Cognitive Operating System - Backend Entry Point.
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from memory.short_term import short_term_memory


# ═══════════════════════════════════════════════════════════════════════════
# Lifespan
# ═══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    # Startup
    print("🧠 Digital Denis starting...")
    print(f"   Language: {settings.system_language}")
    print(f"   Debug: {settings.debug}")
    print(f"   Model: {settings.default_model}")
    
    # Connect to Redis
    await short_term_memory.connect()
    print("   Redis: connected")
    
    yield
    
    # Shutdown
    await short_term_memory.disconnect()
    print("🧠 Digital Denis shutting down...")


# ═══════════════════════════════════════════════════════════════════════════
# Application
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Digital Denis",
    description="Personal Cognitive Operating System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Digital Denis",
        "version": "0.1.0",
        "status": "running",
        "language": settings.system_language,
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "debug": settings.debug,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Include Routers
# ═══════════════════════════════════════════════════════════════════════════

from api.routes import messages, memory

app.include_router(messages.router, prefix="/api/v1/messages", tags=["messages"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])


# ═══════════════════════════════════════════════════════════════════════════
# Run with: uvicorn main:app --reload
# ═══════════════════════════════════════════════════════════════════════════
