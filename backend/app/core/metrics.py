"""Prometheus metrics. Per-stage identify histograms are added in Phase 4."""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

HTTP_REQUESTS = Counter(
    "ansit_http_requests_total",
    "HTTP requests handled.",
    ["method", "route", "status"],
)
HTTP_LATENCY = Histogram(
    "ansit_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
IDENTIFY_TOTAL = Counter(
    "ansit_identify_total",
    "Identify requests by outcome.",
    ["status", "reason", "client"],
)
IDENTIFY_STAGE = Histogram(
    "ansit_identify_stage_duration_seconds",
    "Time spent in each identify stage.",
    ["stage"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.4, 0.8, 1.2, 1.6, 2.0, 2.5, 3.5, 5.0, 10.0),
)
TEXT_CONFIDENCE = Histogram(
    "ansit_text_confidence",
    "Ayah match confidence (0-1) of matched and ambiguous results.",
    buckets=(0.5, 0.6, 0.7, 0.76, 0.8, 0.85, 0.9, 0.95, 0.98, 1.0),
)
RECITER_SIMILARITY = Histogram(
    "ansit_reciter_similarity",
    "Best reciter score, by decision.",
    ["status"],
    buckets=(0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.7, 0.725, 0.75, 0.8, 0.85, 0.9, 1.0),
)
RECITER_TOTAL = Counter("ansit_reciter_total", "Reciter decisions.", ["status"])
RATE_LIMITED = Counter(
    "ansit_rate_limited_total", "Requests rejected by the rate limiter.", ["scope"]
)
IDENTIFY_IN_FLIGHT = Gauge(
    "ansit_identify_in_flight", "Identify requests currently running models."
)
IDENTIFY_REJECTED = Counter(
    "ansit_identify_rejected_total", "Uploads rejected before identification.", ["code"]
)
READY = Gauge("ansit_ready", "1 when startup tasks have completed successfully, else 0.")


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
