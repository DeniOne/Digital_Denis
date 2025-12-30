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
