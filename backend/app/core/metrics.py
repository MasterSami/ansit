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
READY = Gauge("ansit_ready", "1 when startup tasks have completed successfully, else 0.")


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
