# Deployment guide (staging/production checklist)

Audit date: 2026-11-22. No production deployment was performed.

## Runtime requirements

- Python backend image runs as UID 10001, read-only filesystem, `/tmp` tmpfs, and health check. CPU Dockerfile is the reviewed target; GPU target is explicitly untested.
- API requires built Quran index and ASR model; reciter recognition also requires ONNX speaker model and gallery/registry. Verify model licenses and source terms before distribution.
- Web requires Node 22+ at build, then Next.js production server or an approved platform runtime.
- Start with a measured 4-vCPU API instance and no more than two concurrent identify slots pending new load data.

## Configuration

1. Create secrets in the host's secret manager; never copy local `.env` values to production.
2. Set `APP_ENV=prod`, exact `CORS_ORIGINS`, model/index/gallery paths, `DATABASE_URL`, authenticated `REDIS_URL`, rate/concurrency limits, and `TRUST_PROXY_HEADERS=true` only behind a trusted proxy that strips client-supplied forwarding headers.
3. Set database/Redis to private networks; the committed Compose defaults are for local development only.
4. Terminate HTTPS at the reverse proxy, limit request body and timeout consistently with API limits, set TLS/HSTS there, and restrict `/metrics`, `/docs`, and `/openapi.json` as appropriate.
5. Do not enable debug responses in production.

## Release sequence

1. Build artifacts in a reproducible CI job and attach checksums, source revision, and model version.
2. Build and scan the CPU runtime image; this audit did not build the image because Docker was unavailable.
3. Apply Alembic migrations once as a deployment job before starting new replicas. For replicas, set `RUN_MIGRATIONS=false` in the app containers to avoid concurrent startup migrations.
4. Deploy one canary, confirm `/healthz`, `/readyz`, dependency booleans, gallery count, and a synthetic recognition request.
5. Observe error rate, queue timeouts, stage latency, memory, disk, and Redis/database connectivity; roll back the image/artifact revision if readiness or error budgets fail.

## Rollback

Keep the previous immutable image and artifact set. Roll back application and artifact versions together. Only use backward-compatible migrations during the rollback window; destructive schema changes need a separate reviewed migration plan.

## Launch state

Production deployment remains **BLOCKED** on database/Redis/TLS/secret-manager configuration, browser E2E failures, Docker validation, and restore/load verification. This guide is not a claim that the cloud environment exists.
