# Phase 4 — production API (plan)

## What gets built

| Piece          | File                                                        | What                                                         |
| -------------- | ----------------------------------------------------------- | ------------------------------------------------------------ |
| Schemas        | `backend/app/api/schemas.py`                                | Pydantic models for every request and response               |
| Errors         | `backend/app/api/errors.py`                                 | One error shape: `{"error": {"code", "message"}}`            |
| Identify       | `backend/app/api/identify.py`, `app/identify_service.py`    | `POST /v1/identify`                                          |
| Quran          | `backend/app/api/quran.py`                                  | `/v1/surahs`, `/v1/surahs/{n}`, `/v1/ayahs/{surah}/{ayah}`   |
| Reciters       | `backend/app/api/reciters.py`                               | `/v1/reciters`, `/v1/reciters/{id}`                          |
| Feedback       | `backend/app/api/feedback.py`                               | `POST /v1/feedback`                                          |
| Services       | `backend/app/services.py`                                   | Loads index, models and gallery at startup (readiness tasks) |
| Rate limit     | `backend/app/core/ratelimit.py`                             | Per IP and per device, Redis-backed                          |
| Session memory | `backend/app/core/ephemeral.py`                             | Short-lived candidate list for "listen longer"               |
| Tables         | `backend/app/db/models.py`, migration `0002`                | `identify_events`, `feedback`                                |
| Images         | `infra/docker/backend.Dockerfile`, `backend.gpu.Dockerfile` | CPU image (models mounted or baked), optional GPU            |
| Load test      | `infra/locust/locustfile.py`                                | Result recorded in `docs/PROGRESS.md`                        |

## Request flow for `/v1/identify`

1. Rate limit (IP, then device id). 429 with `Retry-After` when exceeded.
2. Read the upload with a hard cap (413 above `MAX_UPLOAD_MB`).
3. Decode in memory; reject undecodable (422) and too-long (422) uploads.
4. Clip shorter than `MIN_CLIP_SEC` → `no_match / too_short`. VAD gate →
   `no_match / no_speech`. Neither model runs for those.
5. **Two branches at the same time on the same waveform**, each in its own
   worker thread: ASR → guards → ayah match, and speaker embedding → gallery
   decision. CTranslate2 and ONNX Runtime get explicit thread counts
   (`CPU_THREADS_ASR`, `CPU_THREADS_SPEAKER`) so that together they do not
   exceed the cores.
6. If the ayah branch finds no recitation, the reciter is not reported.
7. Fuse into the response; record metrics and an `identify_events` row.

A semaphore bounds how many identify requests run the models at once
(`MAX_CONCURRENT_IDENTIFY`); a request that cannot start within
`IDENTIFY_QUEUE_TIMEOUT_SEC` gets 503 instead of piling up.

## Design decisions

- **Privacy without temp files.** The brief asks for temp files on tmpfs
  removed in `finally`. Since Phase 2 the clip is decoded from memory and never
  written anywhere, which is stronger; there is nothing to clean up. A test
  asserts that a request leaves no file behind, and another that neither audio
  nor transcript appears in the logs. The container still runs read-only with
  `/tmp` on tmpfs.
- **"Listen longer" without storing a transcript.** When a result is
  ambiguous, the _positions_ of its candidate locations are kept for a few
  minutes under the identify id (Redis, or process memory without Redis). A
  follow-up request with `previous_identify_id` is matched on its own; if
  exactly one earlier candidate is immediately followed by a location of the
  new clip, the result is resolved to that location. No transcript or audio
  is kept, and the gap while the user waited does not matter.
- **`identify_events` holds no audio and no transcript**: status, reason,
  scores, clip length, timings, client, app version, and the reciter id.
- **Gallery and registry source.** Postgres when `DATABASE_URL` is set and the
  gallery tables have rows; otherwise the files named by `GALLERY_PATH` /
  `REGISTRY_PATH`. This keeps development possible without Postgres. With
  neither, the service still identifies ayahs and reports the reciter as
  unknown.
- **Rate limiting.** Fixed one-minute windows per IP and per `X-Device-ID`.
  With Redis it is shared across instances; without `REDIS_URL` an in-process
  limiter is used (single instance only). If Redis is configured but
  unreachable the request is allowed and a warning is logged: an outage of the
  limiter should not take identification down.
- **Client IP** is the socket peer unless `TRUST_PROXY_HEADERS=true`, in which
  case the first `X-Forwarded-For` entry is used. Off by default because the
  header is trivially spoofed when there is no trusted proxy in front.
- **Reciter in the response.** `identified`: id, name, style, similarity and up
  to two alternatives. `unknown`: no id or name, plus up to two best guesses
  as alternatives for the "may also be" line.
- **Audio links.** `/v1/reciters/{id}` returns per-ayah URL templates built
  from the EveryAyah folders (pattern verified in Phase 2). mp3quran
  full-surah links are **not** returned yet: their URL pattern has not been
  fetched and checked.
- **Models in the image.** The image expects artifacts under
  `/app/artifacts`. By default that is a read-only volume; a `baked` build
  target copies them in. Both documented in the Dockerfile.
- **Debug output** only when the request asks for it _and_ the server has
  `ALLOW_DEBUG=true`.

## Tests

- API tests run with a scripted ASR engine, a scripted speaker engine and a
  small synthetic gallery, on synthetic audio, against the real Quran index.
  No recitation audio is committed, so the "golden audio fixtures" are
  generated in the test, not stored.
- Tests against the real models run locally when the artifacts exist.
- Database-backed behaviour (events, feedback, gallery from Postgres) runs
  against the pgvector service in CI.

## Risks

- The load test runs on this 4-vCPU machine with the client on the same host,
  so the client competes for CPU with the server.
- The GPU Dockerfile cannot be built or run here (no GPU); it is provided
  untested and marked as such.
- k6 is not available in this environment; Locust is used instead, which the
  brief allows.

## Done when

Endpoints implemented and documented in `docs/API.md`, tests green in CI, load
test result in `docs/PROGRESS.md`. Then stop.

## What changed during the phase

**Thread counts came from the load test, not from the plan.** The first
defaults were one request at a time with 3 ASR threads + 1 speaker thread.
Measured with one user sending clips back to back (60 s runs, mixed 5/8/12 s
phone-like clips):

| ASR threads (speaker 1, one request at a time) | p50    | p95   | Requests/s |
| ---------------------------------------------- | ------ | ----- | ---------- |
| 2                                              | 0.89 s | 1.2 s | 1.15       |
| 3                                              | 1.2 s  | 1.9 s | 0.80       |
| 4                                              | 1.3 s  | 2.0 s | 0.76       |

More ASR threads made a request _slower_ once the speaker branch ran beside
it on a 4-core machine. With 2 threads there is room for a second request in
parallel, so the defaults became `CPU_THREADS_ASR=2`, `CPU_THREADS_SPEAKER=1`,
`MAX_CONCURRENT_IDENTIFY=2`, and the ASR engine gets as many workers as there
are slots. The full results are in `docs/PROGRESS.md`.

**Uploads above 1 MB would have been written to a temporary file** by the web
framework's multipart parser, which spools large parts to disk. The request
body is now capped before parsing and the parser keeps that much in memory, so
the clip stays in RAM. A test uploads a 1.7 MB file and fails if a spool file
is ever created.

**Image size grew** from 305 MB (Phase 0 skeleton) to 948 MB with the ASR and
ONNX runtimes. Model files are extra: about 110 MB mounted or baked.
