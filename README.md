# Ansit (أنصِت)

Listens to a short Quran recitation (5–15 s) and returns the surah, the ayah and
the reciter's name.

Status: **Phases 0–3 complete** (scaffolding, ayah matcher, ASR pipeline, reciter identification). No HTTP endpoint for identification yet. See [`docs/PROGRESS.md`](docs/PROGRESS.md).

## Quick start

Requires Docker, [uv](https://docs.astral.sh/uv/) and `make`.

```bash
make setup   # backend deps, .env from .env.example, git hooks
make up      # postgres+pgvector, redis, backend → http://localhost:8000
make check   # ruff + mypy + pytest
```

`make help` lists every target.

## Layout

| Path       | What                                                                     |
| ---------- | ------------------------------------------------------------------------ |
| `backend/` | FastAPI service (Python 3.11+, uv, ruff, mypy, pytest)                   |
| `ml/`      | Offline scripts: data download, index build, gallery build, evaluation   |
| `web/`     | Next.js app (Phase 5)                                                    |
| `mobile/`  | Flutter app (Phase 6)                                                    |
| `infra/`   | docker-compose, Dockerfiles, load tests                                  |
| `docs/`    | Plans per phase, progress log, API and data-source notes, design mockups |

## Privacy

The microphone is used only when the user taps Listen, and the clip is deleted
right after identification. The backend never persists audio and never logs
audio bytes or transcripts at INFO level.
