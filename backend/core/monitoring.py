"""
Digital Denis — Monitoring & Metrics
═══════════════════════════════════════════════════════════════════════════

Prometheus metrics definitions and collection utilities.
"""

from prometheus_client import Counter, Histogram, Gauge

# ─────────────────────────────────────────────────────────────────────────────
# HTTP Metrics
# ─────────────────────────────────────────────────────────────────────────────

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total count of HTTP requests",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

import re

def sanitize_path(path: str) -> str:
    """
    Sanitize URL path for Prometheus labels.
    Replaces UUIDs and numeric IDs with placeholders to avoid high cardinality.
    """
    # Replace UUIDs
    path = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '{id}', path)
    # Replace numeric IDs (if any)
    path = re.sub(r'/\d+/', '/{id}/', path)
    if path.endswith('/') and len(path) > 1:
        path = path[:-1]
    return path

# ─────────────────────────────────────────────────────────────────────────────
# Application Metrics
# ─────────────────────────────────────────────────────────────────────────────

LLM_TOKENS_TOTAL = Counter(
    "llm_tokens_total",
    "Total number of tokens processed by LLM",
    ["model", "type"]  # type: input, output
)

MEMORY_ITEMS_TOTAL = Gauge(
    "memory_items_total",
    "Total number of items in long-term memory",
    ["user_id"]
)

ANOMALIES_DETECTED = Counter(
    "anomalies_detected_total",
    "Total number of anomalies detected",
    ["type", "severity"]
)

ACTIVE_SESSIONS = Gauge(
    "active_sessions",
    "Number of currently active user sessions"
)
