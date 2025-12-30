"""
Digital Denis — Structured Logging
═══════════════════════════════════════════════════════════════════════════

Configures structlog for JSON output in production and colored console output
during development.
"""

import logging
import sys
import structlog
from typing import Any, Dict

from core.config import settings


def configure_logging() -> None:
    """Configure structlog and standard logging."""
    
    # Common processors for all environments
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # JSON renderer for production (or if configured)
    if not settings.debug:
        processors.extend([
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ])
    else:
        # User-friendly colored output for development
        processors.extend([
            structlog.dev.ConsoleRenderer()
        ])

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger."""
    return structlog.get_logger(name)
