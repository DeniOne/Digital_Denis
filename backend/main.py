"""
Digital Denis — Backend API
═══════════════════════════════════════════════════════════════════════════

Personal Cognitive Operating System - Backend Entry Point.
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import time

from core.config import settings
from core.logging import configure_logging, get_logger
from core.monitoring import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION_SECONDS
from memory.short_term import short_term_memory

# Configure logging
configure_logging()
logger = get_logger(__name__)


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



@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """Middleware to log requests and record metrics."""
    start_time = time.time()
    from core.monitoring import sanitize_path
    path = sanitize_path(request.url.path)
    method = request.method
    
    # Skip logging for metrics endpoint to avoid noise
    if path == "/metrics":
        return await call_next(request)
        
    response = await call_next(request)
    
    duration = time.time() - start_time
    status = response.status_code
    
    # Record metrics
    HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=path, status=status).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=path).observe(duration)
    
    # Log details
    logger.info(
        "http_request",
        method=method,
        path=path,
        status=status,
        duration=f"{duration:.3f}s",
        user_agent=request.headers.get("user-agent"),
    )
    
    return response


# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    # Skip security headers for documentation and preflight OPTIONS requests
    if request.method == "OPTIONS" or request.url.path.startswith("/docs") or request.url.path.startswith("/redoc") or request.url.path == "/openapi.json":
        return await call_next(request)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Allow Swagger UI resources
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://telegram.org https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "frame-src 'self' https://oauth.telegram.org;"
    )
    return response


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

from api.routes import api_router

app.include_router(api_router)


# ═══════════════════════════════════════════════════════════════════════════
# CORS & Outermost Middleware
# ═══════════════════════════════════════════════════════════════════════════

# CORS Middleware - Must be added LAST to be the outermost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://digital-denis.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════
# Run with: uvicorn main:app --reload
# ═══════════════════════════════════════════════════════════════════════════
