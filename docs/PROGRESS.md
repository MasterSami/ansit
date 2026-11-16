# Progress

## Phase 0 — Scaffolding · complete, awaiting review

Plan: [`plans/phase-0.md`](plans/phase-0.md)

### What was built

- Monorepo layout from the brief, `Makefile`, `.env.example`, pre-commit config, CI workflow.
- Backend skeleton: app factory, `/healthz`, `/readyz`, `/metrics`, structlog JSON
  logging with request IDs, pydantic-settings config covering every variable in
  brief §6.
- `/readyz` is driven by named startup tasks run in the background during
  lifespan (the hook where model loading plugs in from Phase 2), plus Postgres
  and Redis pings when their URLs are configured.
- `infra/docker-compose.yml`: `pgvector/pgvector:pg16`, `redis:7-alpine`, backend
  image (non-root, read-only root filesystem, `/tmp` on tmpfs).
- Design mockups copied to `docs/design/`.

### Verification (run on 2026-11-16, 4 vCPU Linux, Python 3.12.3)

| Check                                              | Result                                                       |
| -------------------------------------------------- | ------------------------------------------------------------ |
| `ruff check` + `ruff format --check` (backend, ml) | clean                                                        |
| `mypy` (strict on `app/`)                          | clean, 21 source files                                       |
| `pytest`                                           | 19 passed                                                    |
| `pre-commit run --all-files` (incl. prettier)      | all 10 hooks pass                                            |
| `make up`                                          | postgres, redis, backend all reach `healthy`                 |
| `GET /readyz` on the running stack                 | `200`, `database: true`, `redis: true`                       |
| `GET /readyz` with redis stopped                   | `503`, `redis: false`                                        |
| pgvector                                           | extension `vector` 0.8.7 present in the `ansit` database     |
| Backend container                                  | runs as uid 10001; writes outside `/tmp` fail (read-only fs) |
| Backend image size                                 | 305 MB                                                       |

No accuracy or latency targets apply to this phase.

### Decisions

- Startup tasks run in a background task, not inline in lifespan, so `/healthz`
  answers while models load and `/readyz` reports 503 with per-component state.
- A failed startup task leaves the service permanently not-ready (and logged)
  rather than crashing the process; the orchestrator sees it through `/readyz`.
- Route _templates_ are used as metric labels, with `unmatched` for 404s.
- `uv` is installed in the image from PyPI (`pip install uv==0.11.32`) rather
  than copied from `ghcr.io`, so the build depends on one registry less.
- `web/` and `mobile/` are placeholders until Phases 5 and 6. Their CI jobs
  exist and skip themselves until the projects are created.

### Open issues

1. **CI has not run.** There is no GitHub remote for this repository yet, so
   the workflow is unobserved. The same commands pass locally. "CI is green"
   from the Phase 0 done-criteria is therefore **not confirmed**.
2. **The repository is not pushed anywhere.** It exists only in this working
   environment until a remote is added.
3. **Image build in this environment needed local help** that is not part of
   the repo: Docker Hub returned 429 (rate limit), so base images were pulled
   from `mirror.gcr.io`, and the build container reached PyPI through the
   environment's proxy via a locally built base image. On a normal machine or
   on GitHub Actions the committed Dockerfile should build as is — unverified.
4. **Flutter is not installed here.** Phase 6 needs a machine with the Flutter
   SDK, or the SDK added to this environment.
5. `MATCH_THRESHOLD`, `AMBIGUITY_DELTA` and `RECITER_THRESHOLD` are placeholder
   values, not calibrated. Phases 1 and 3 set them from evaluation data.
6. No database tables or migrations yet; Alembic is introduced with the first
   tables.

### Next

Phase 1 — Quran text, normalization, ayah matcher, text-only evaluation.
Not started; waiting for review.
