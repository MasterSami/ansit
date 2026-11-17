# Ansit (أنصِت)

Listens to a short Quran recitation (5–15 s) and returns the surah, the ayah and
the reciter's name.

Status: **Phases 0–6 complete**: the backend identifies surah, ayah and reciter over HTTP; the web app (`web/`) is usable in a browser; the Flutter app (`mobile/`) passes its tests and CI builds an Android APK, but it has not yet been run on a real phone. See [`docs/PROGRESS.md`](docs/PROGRESS.md).

## Quick start

Requires [uv](https://docs.astral.sh/uv/) and `make`. Docker is optional.

### 1. Build the artifacts (once)

Model files, the Quran index and the reciter gallery are not in the
repository; they are built from their sources.

```bash
make setup          # backend deps, .env from .env.example, git hooks
make data index     # Quran text from Tanzil, then the search index
make models         # ASR models -> CTranslate2 (downloads PyTorch CPU for the conversion)
make speaker-model  # speaker embedding model (27 MB)
make gallery        # reciter gallery: downloads ~620 MB of recitation, takes ~25 min
```

To try ayah identification without waiting for the gallery, skip the last
step and run with `RECITER_ENABLED=false`.

### 2. Run it

Without Docker (no Postgres or Redis needed):

```bash
make serve          # http://localhost:8000  (PORT=8080 make serve for another port)
```

With Docker (Postgres + pgvector, Redis and the API):

```bash
make up
make gallery-db DATABASE_URL=postgresql+asyncpg://ansit:ansit@localhost:5432/ansit
```

Then open `http://localhost:8000/docs` and use `POST /v1/identify` to upload a
short recording, or:

```bash
curl -F "audio=@clip.m4a" http://localhost:8000/v1/identify
```

`make check` runs lint, type-check and tests. `make help` lists every target.
API reference: [`docs/API.md`](docs/API.md).

## Layout

| Path       | What                                                                     |
| ---------- | ------------------------------------------------------------------------ |
| `backend/` | FastAPI service (Python 3.11+, uv, ruff, mypy, pytest)                   |
| `ml/`      | Offline scripts: data download, index build, gallery build, evaluation   |
| `web/`     | Next.js web app (PWA)                                                    |
| `mobile/`  | Flutter app (Phase 6)                                                    |
| `infra/`   | docker-compose, Dockerfiles, load tests                                  |
| `docs/`    | Plans per phase, progress log, API and data-source notes, design mockups |

## Privacy

The microphone is used only when the user taps Listen, and the clip is deleted
right after identification. The backend never persists audio and never logs
audio bytes or transcripts at INFO level.
