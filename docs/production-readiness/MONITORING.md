# Monitoring and alerting

Audit date: 2026-11-22. The API exposes Prometheus metrics and structured logs; no dashboard or external alert service is configured here.

## Existing signals

- Liveness `/healthz`, readiness `/readyz`, metrics `/metrics`.
- HTTP request count and latency by method/route/status; identify totals, stage duration, confidence/similarity distributions, in-flight work, rejections/rate-limits, and ready gauge.
- Structured JSON request logs carry a validated request ID and route/status/duration. Audio bytes/transcripts are excluded.
- Readiness reports configured Postgres/Redis and model/index/gallery startup state.

## Suggested initial alerts (operational starting points, not yet measured SLOs)

| Signal | Initial trigger | Response |
|---|---|---|
| Readiness | not ready for >2 minutes after deploy | inspect artifact load, DB/Redis reachability, rollback if persistent |
| 5xx / identify failures | >2% for 5 minutes, minimum traffic threshold | correlate by request ID; inspect model/dependency logs |
| Identify p95 | >2.5 s for 10 minutes | compare ASR/speaker stages and queueing; reduce ingress or scale after measurement |
| Busy/queue timeout | >1% of identify requests over 5 minutes | cap incoming requests and review concurrency/CPU |
| Redis limiter warning | any sustained warning for 2 minutes | restore Redis; note process-local degraded enforcement |
| Host pressure | CPU >85% for 10 minutes, memory >85%, disk >80% | inspect inference saturation, logs, artifacts and DB growth |
| Error budget | alert when monthly availability target is breached | target must be agreed before launch |

Do not expose `/metrics` publicly without an ingress policy. Add dashboards for deployment/version, request latency, stage latency, status codes, in-flight requests, readiness components, Redis/DB health, and host CPU/RAM/disk. These thresholds are proposals; tune them from production-like baselines.
