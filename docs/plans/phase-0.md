# Phase 0 — Scaffolding (plan)

## Goal

A monorepo where `make up` starts postgres+pgvector, redis and the backend, the
backend exposes `/healthz`, `/readyz`, `/metrics` with structured JSON logs and
request IDs, and lint + type-check + tests are wired locally, in pre-commit and in CI.

## What gets built

| Area    | Files                                                                                                                                                                                                                                  |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Repo    | `Makefile`, `.gitignore`, `.editorconfig`, `.env.example`, `.pre-commit-config.yaml`, `ruff.toml`, `README.md`                                                                                                                         |
| Backend | `backend/pyproject.toml` (uv), `app/main.py` (app factory + lifespan), `app/core/{config,logging,metrics,readiness,middleware,dependencies}.py`, `app/api/health.py`, empty packages for `audio/ asr/ matcher/ speaker/ db/`, `tests/` |
| Infra   | `infra/docker-compose.yml`, `infra/docker/backend.Dockerfile`                                                                                                                                                                          |
| CI      | `.github/workflows/ci.yml` — backend (ruff, mypy strict, pytest), image build, web and mobile jobs that activate once those projects exist                                                                                             |
| Docs    | `docs/PROGRESS.md`, `docs/API.md`, `docs/DATA_SOURCES.md` (stub, filled in Phase 1), `docs/design/*.dc.html` (reference mockups)                                                                                                       |

## Design decisions

- **Readiness model.** Startup work (model loading in later phases) is a list of
  named `StartupTask`s run in a background task during the FastAPI lifespan.
  `/healthz` is live immediately; `/readyz` returns 503 until every task has
  finished successfully, and stays 503 if one fails. Phase 0 registers no tasks,
  so the mechanism is exercised by tests with fake slow/failing tasks.
- **Dependency checks.** `/readyz` also pings Postgres (`SELECT 1`) and Redis
  (`PING`) when `DATABASE_URL` / `REDIS_URL` are set, each with a 1 s timeout.
  Unset URLs are skipped so unit tests need no services.
- **Request IDs.** Pure-ASGI middleware. Accepts a sane incoming `X-Request-ID`
  (≤ 64 chars, `[A-Za-z0-9._-]`), otherwise generates a UUID4; binds it to
  structlog contextvars; echoes it on the response.
- **Metrics.** `prometheus-client`; an HTTP request counter and latency histogram
  labelled by method, _route template_ (not raw path, to bound cardinality) and
  status. Per-stage histograms come in Phase 4.
- **Config.** `pydantic-settings`, every name in brief §6 present from day one.
  `MATCH_THRESHOLD`, `AMBIGUITY_DELTA`, `RECITER_THRESHOLD` have placeholder
  defaults that are explicitly uncalibrated until Phases 1 and 3.
- **Python version.** `requires-python >= 3.11`; Docker image and CI use 3.12
  (best wheel coverage for torch / ctranslate2 / speechbrain in later phases).
- **Lint config** lives in a root `ruff.toml` so `backend/` and `ml/` share it.

## Deliberately deferred

- `web/` and `mobile/` are placeholders (README only). The Next.js and Flutter
  projects are created in Phases 5 and 6; their CI jobs are already present and
  skip themselves until `web/package.json` / `mobile/pubspec.yaml` exist.
- No SQLAlchemy models or Alembic migrations yet (first tables arrive in Phase 3).
- `make data | index | gallery | eval` exist as targets but only print which
  phase implements them.
- ffmpeg is not in the image yet (added in Phase 2 with the audio pipeline).

## Risks

- **CI cannot be observed from this environment** — there is no GitHub remote.
  I will run the exact CI commands locally and say so; "CI green" needs
  confirming after the first push.
- Docker builds here go through an egress proxy; if the image build cannot reach
  PyPI from inside the build container, I will report it rather than work around
  it in the Dockerfile.

## Done when

`make up` brings all three services to healthy, `/readyz` returns 200, ruff +
mypy + pytest pass, and `docs/PROGRESS.md` records the result.
