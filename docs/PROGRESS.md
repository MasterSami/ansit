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

### Open issues at the end of Phase 0 — status

1. ~~CI has not run~~ — resolved. The repository is at
   `github.com/MasterSami/ansit`; the first run on `main` passed all four jobs.
2. ~~Not pushed anywhere~~ — resolved (same).
3. ~~Dockerfile unverified outside this environment~~ — resolved: the image
   built on GitHub Actions from the committed Dockerfile unchanged.
4. **Flutter is not installed here.** Still open; matters in Phase 6.
5. `RECITER_THRESHOLD` is still a placeholder (Phase 3). `MATCH_THRESHOLD` and
   `AMBIGUITY_DELTA` were set in Phase 1, see below.
6. No database tables or migrations yet; Alembic arrives with the first tables.

## Phase 1 — Quran text, normalization, ayah matcher · complete, awaiting review

Plan: [`plans/phase-1.md`](plans/phase-1.md) ·
Full report: [`../ml/eval/reports/phase1.md`](../ml/eval/reports/phase1.md)

### What was built

- `ml/scripts/download_quran.py` — fetches the three Tanzil files, records
  SHA-256, runs the integrity checks.
- `app/matcher/quran_data.py` — loader. Fails loudly unless there are exactly
  114 surahs and 6,236 ayahs with per-surah counts matching the metadata, 30
  juz, 604 pages, and both text files agreeing.
- `app/matcher/normalize.py` — `normalize_ar`, with a configurable
  standalone-hamza rule.
- `app/matcher/index.py` + `ml/scripts/build_index.py` — global word sequence,
  1/2/3-gram postings, duplicate groups; artifact
  `ml/artifacts/quran_index.json.gz` (529 KB, loads in about 240 ms).
- `app/matcher/search.py` — offset voting, character-level alignment, span
  mapping, ambiguity, no-match.
- `ml/eval/text_eval.py` — the evaluation; `make data | index | eval` now work.
- 61 new tests (80 total). No Quran text is typed anywhere: tests name ayahs by
  number and read the text from the data; the isti'adha is assembled from
  words of 113:1 and 16:98.

The matcher is a library in this phase. It is not wired into an API endpoint
yet; that is Phase 4.

### Results (4 vCPU x86_64, Python 3.12.3, seed 20261116)

| Target                                  | Result                     | Verdict |
| --------------------------------------- | -------------------------- | ------- |
| Top-1 ≥ 95% at WER 10%, spans ≥ 8 words | 99.3% (1,602 unique spans) | met     |
| p95 search latency < 50 ms              | 5.04 ms                    | met     |

Top-1 on unique spans of all lengths (4–25 words), by nominal WER:

| WER                                  | 0%     | 5%    | 10%   | 15%   | 20%   |
| ------------------------------------ | ------ | ----- | ----- | ----- | ----- |
| Top-1                                | 100.0% | 99.2% | 98.7% | 98.5% | 96.6% |
| Top-3                                | 100.0% | 99.4% | 98.9% | 98.9% | 97.6% |
| Wrong ayah reported as a plain match | 0.0%   | 0.7%  | 0.8%  | 1.0%  | 1.7%  |

Other measurements:

- Short spans (under 8 words) are the weak spot: 96.4% top-1 at WER 10%,
  92.3% at WER 20%.
- Repeated phrases (36 of 2,000 spans): reported as ambiguous with the true
  location listed in 100% of cases at WER 0% and 10%, 91.7% at WER 15–20%.
- Isti'adha / basmala before a surah: true location offered in 100% of clean
  clips and 98.0–99.3% at WER 10%.
- Basmala in the middle of a clip: 100% clean, 95.9% at WER 10%.
- Search latency p50 2.0 ms, p99 6.6 ms, worst single query 115 ms.

### Verified about the data

- Tanzil text and metadata have the format and counts the brief assumed.
- **The basmala is embedded in ayah 1 of 112 surahs** in both files, and two
  of them (95, 97) spell it differently in Uthmani. The loader splits it off
  and keeps the Uthmani prefix verbatim in a separate field.
- License is CC BY 3.0 with a verbatim-only condition; details and what it
  obliges the UI to do are in [`DATA_SOURCES.md`](DATA_SOURCES.md).
- `tanzil.net` was blocked by this environment's network rules; a separate
  `ansit` environment allowing that one host was created with approval.

### Decisions

- **`MATCH_THRESHOLD = 76`** (0–100 scale): the lowest score that accepts at
  most 1% of random Quran-vocabulary word sequences. It rejects 0.1% of true
  spans at WER 10% and 1.3% at WER 20%. Provisional until Phase 2.
- **`AMBIGUITY_DELTA = 2`** kept. In the sweep, values from 0 to 5 change the
  wrong-match rate by 0.1 points while 5 triples the ambiguous prompts.
- **Standalone hamza = `merge_madd`.** The three settings are within 0.1
  points of each other on accuracy, so this is a weak preference: it matches
  Uthmani spelling as well as `drop` (39.4% of ayahs identical, against 36.1%
  for `keep`) without merging 34 distinct words the way `drop` does.
- **Ambiguity is based on the matched words**, not only whole-ayah duplicates:
  if the matched word sequence occurs more than once anywhere, the result is
  ambiguous and `repeated_count` is the exact number of occurrences.
- **Artifact is gzip JSON, not pickle**, and stores the corpus rather than the
  postings, which are rebuilt at load. Safe to load, byte-identical rebuilds.
- `prefix_detected` can also be `"isti'adha+basmala"`, an addition to the two
  values in the brief.

### Two problems found by the evaluation and fixed

- Span edges spilled onto a neighbouring word when the query was longer than
  the true text, which could tip the primary ayah to a neighbour. Edges are
  now re-aligned word by word. Top-1 at WER 10% (spans ≥ 8 words) went from
  98.3% to 99.3%.
- A basmala between two surahs was not handled: 57.3% on clean text. The
  matcher now also tries the query with it removed: 100%.

Both have regression tests.

### Open issues

1. **Synthetic noise is not ASR noise.** These numbers show the matcher works
   on text; they do not predict end-to-end accuracy. Phase 2 measures that.
2. **Uthmani-style spelling is a real risk for Phase 2.** Only 39.4% of ayahs
   normalize to the same string from the Uthmani and simple files (mean
   character similarity 98.9). If the ASR model writes Uthmani-like spelling,
   most words still match, but the gap should be measured on real output and
   may need extra folding rules.
3. **Short clips.** Four to seven words is where accuracy drops; a 5-second
   clip of slow recitation can be that short.
4. **Negatives are synthetic.** The threshold was chosen against shuffled
   Quran words, not non-Quran speech or ASR hallucinations.
5. The Tanzil terms require crediting Tanzil Project with a link to
   tanzil.net wherever the text is shown. Not yet relevant (no UI), must be
   done in Phases 5 and 6.
6. Carried over: Flutter not installed here; `RECITER_THRESHOLD` placeholder;
   no database tables yet.

### Next

Phase 2 — done, see below.

## Phase 2 — ASR and end-to-end ayah identification · complete, awaiting review

Plan and decisions: [`plans/phase-2.md`](plans/phase-2.md) ·
Full report: [`../ml/eval/reports/phase2.md`](../ml/eval/reports/phase2.md)

### What was built

- `app/audio/decode.py` — webm/opus, m4a/aac, mp3, wav → 16 kHz mono, decoded
  in memory with PyAV. The clip never touches disk.
- `app/audio/vad.py` — Silero VAD used as a gate.
- `app/asr/` — `ASREngine` interface, faster-whisper implementation,
  hallucination guards.
- `app/pipeline.py` — decode → VAD → ASR → guards → match, with per-stage
  timings and the limits from the brief (3–15 s, 2 MB, 1.5 s of speech).
- `ml/scripts/convert_models.py` — Hugging Face → CTranslate2 int8, pinned
  to commits.
- `ml/eval/build_audio_eval.py`, `ml/eval/audio_eval.py`, `ml/eval/heldout.py`.
- 40 new tests (120 total). The pipeline is tested with a scripted ASR engine
  and synthetic audio; one test runs the real models when they are built
  locally and is skipped otherwise.

Still a library. Nothing new is reachable over HTTP until Phase 4.

### Results (`tarteel-base`, 4 vCPU x86_64, int8, one request at a time)

| Target                         | Result                | Verdict     |
| ------------------------------ | --------------------- | ----------- |
| Top-1 ≥ 90% on clean 8 s clips | **87.5%** (168 clips) | **NOT met** |
| End-to-end p95 < 2.5 s         | 2.17 s (1,232 clips)  | met         |

Top-1 = the reported ayah is actually heard in the clip.

| Condition  | 5 s   | 8 s   | 12 s  |
| ---------- | ----- | ----- | ----- |
| clean      | 78.6% | 87.5% | 93.5% |
| phone-like | 53.0% | 73.8% | 81.0% |

- **Confidently wrong answers are rare**: status `match` naming an ayah not in
  the clip happened in 0.0–1.8% of clips depending on condition.
- **On clean 8 s clips the miss is mostly ambiguity, not error.** Of the 21
  clips that were not Top-1, 15 came back `ambiguous`; counting an ambiguous
  result that lists the true location as acceptable gives 94.6%. Slow
  reciters say only two or three words in 8 s, and those words often occur
  in several places.
- **Mujawwad is much harder**: 58.3% clean, 30.6% phone-like (36 clips each),
  for the same reason — too few words per clip.
- **One reciter scores 0%** (`Abdullaah_3awwaad_Al-Juhaynee_128kbps`), with
  all three models, even on whole ayahs. Cause not established. Without that
  folder clean 8 s Top-1 is 90.7%; it stays in the reported result.
- **Clips that open with a basmala**: 53.9% clean. The basmala uses up most
  of an 8 s clip, and when only a one-word opening follows, the transcript is
  a single word and is rejected as too short.
- **Non-speech** (silence, noise, tones): 60 of 60 rejected.
- Latency by clip length, p95: 1.33 s (5 s), 1.78 s (8 s), 2.39 s (12 s).
  ASR is almost all of it; decode, VAD and matching together are under 70 ms.

### Three things these numbers do not show

1. **The models were trained on the same recordings.** EveryAyah is their
   training data and its splits share reciters. These are results on studio
   recordings of famous reciters the model has heard: an upper bound.
2. **The phone condition is simulated** (synthetic reverb, noise, band-limit,
   Opus). No real recordings of a phone near a speaker.
3. **No non-Quran speech was tested.** Ordinary Arabic speech, a sermon or a
   song could be accepted as a match; that rate is unknown.

### Decisions

- **Model: `tarteel-base`.** `deepdml-small` is 7 points better on phone-like
  audio (81.0% against 73.8%) but takes 2.20 s at p95 on 8 s clips with all
  four cores, before the speaker branch is added. `tarteel-tiny` drops to
  53.6% on phone-like audio. Details in the plan.
- **VAD is a gate only, threshold 0.15, no trimming.** With the usual 0.5 and
  trimming, the first full run scored 83.9% clean and 45.8% phone on 8 s
  clips, because Silero rejected or cut real recitation. This departs from the
  brief's "trim silence". Experiments are in the plan.
- **PyAV instead of an ffmpeg subprocess** for decoding: in memory, no temp
  files, handles iOS M4A, no binary in the image.
- **EveryAyah fetched per ayah from everyayah.com** (82 MB) instead of the
  117 GB Hugging Face dataset.
- **No temperature fallback** in decoding; guards reject weak output instead.
- `MATCH_THRESHOLD` stays at 76. On audio, the match score does not separate
  right from wrong well enough for a higher threshold to pay off.

### Environment changes made with approval

The `ansit` cloud environment now also allows `huggingface.co`,
`datasets-server.huggingface.co`, `us.aws.cdn.hf.co`, `everyayah.com`,
`download.pytorch.org` and `download-r2.pytorch.org`.

### Open issues

1. **Accuracy target missed** (87.5% against 90%). Options:
   - accept "truth offered" as the measure (94.6%), since the remaining
     misses are honest ambiguity that the UI already handles;
   - record longer by default (12 s gives 93.5%);
   - switch to `deepdml-small` and accept a higher latency;
   - on an ambiguous result, automatically listen for more audio.
2. **No independent test data.** Until there are recordings the models have
   not seen (other reciters, real phone captures), true accuracy is unknown.
   A small set of real recordings from the target use would be worth more
   than anything else here.
3. **No non-Quran speech negatives.** Needs a source of ordinary Arabic
   speech; Common Voice Arabic is the obvious one but is a large download.
4. **EveryAyah audio has no stated license.** Treated as not redistributable.
5. **The model tests do not run in CI** (no model there).
6. One-word transcripts are rejected, which loses surah openings such as the
   disjoint letters.
7. The Tarteel models leave a recited basmala out of the transcript, so
   `prefix_detected` is rarely set on real audio.
8. Carried over: Flutter not installed here; `RECITER_THRESHOLD` placeholder;
   no database tables yet; Tanzil attribution due in the UI phases.

### Decision on the missed accuracy target (owner's call, 2026-11-17)

Asked which option to take, the owner said to pick the best one without
changing the model, for resource reasons. Chosen: **judge ayah identification
by "truth offered"** — a correct match, or an ambiguous result that lists the
right location — which is 94.6% on clean 8 s clips, and keep `tarteel-base`.
The remaining misses are honest ambiguity that the ambiguity screen already
handles, and this costs no latency or memory. Strict Top-1 stays reported
next to it.

### Next

Phase 3 — done, see below.

## Phase 3 — reciter identification (open-set) · complete, awaiting review

Plan, experiments and decisions: [`plans/phase-3.md`](plans/phase-3.md) ·
Full report: [`../ml/eval/reports/phase3.md`](../ml/eval/reports/phase3.md)

This section describes the second version. After the first review the owner
asked for fewer known reciters coming back as unknown; the embedding model was
changed and a projection added. The first version's numbers are kept in the
plan for comparison.

### What was built

- `app/speaker/` — NumPy Kaldi filterbank features, WeSpeaker ResNet34 on
  ONNX Runtime behind a `SpeakerEngine` interface, an in-memory gallery with
  LDA projection, scoring and the open-set decision, and persistence in
  Postgres.
- `app/db/` — tables `reciters`, `gallery_clips`, `reciter_centroids` with
  `vector(256)` columns, and the first Alembic migration.
- `ml/registry/reciters.json` — 35 reciters, 39 voices (reciter × style),
  names from the mp3quran API.
- `ml/scripts/` — `fetch_speaker_model.py`, `build_registry.py`,
  `build_gallery.py`, `load_gallery_db.py`. Adding a reciter is
  `make gallery RECITER=id`; nothing is retrained.
- `ml/eval/reciter_eval.py` and its report.
- 36 new tests (156 total), including persistence tests against a real
  Postgres with pgvector, which CI runs as a service.

Still a library; both branches are joined into one request in Phase 4.

### Results

| Target                                       | Result                                         | Verdict |
| -------------------------------------------- | ---------------------------------------------- | ------- |
| False accept ≤ 5% on out-of-gallery reciters | 4.1% (two-fold, 1,232 test clips, 26 reciters) | met     |

At that setting, for a reciter who is in the gallery:

|                       | All clips | Clean | Phone-like | First version, all clips |
| --------------------- | --------- | ----- | ---------- | ------------------------ |
| Named correctly       | 82.5%     | 91.2% | 73.9%      | 71.8%                    |
| Named as someone else | 0.5%      | 0.8%  | 0.2%       | 0.5%                     |
| Returned as unknown   | 17.0%     | 8.0%  | 26.0%      | 27.7%                    |

- Closed-set Top-1 (no rejection): 95.5%. EER: 3.08% (2.27% clean, 3.90%
  phone-like).
- Longer clips help: unknown 23.8% at 5 s, 19.2% at 8 s, 9.6% at 12 s.
- In the 12 s slice alone, false accepts are 5.6%; the 5% target holds over
  all lengths together.
- Embedding time: 170 ms p50 on an 8 s clip with 4 threads. Model file 27 MB.
  **The service still needs no PyTorch.**

### Hard cases, documented honestly

- **Same reciter, different style.** With a reciter's own style removed from
  the gallery, they are ranked first in 23–91% of clips but named (passing
  the threshold) in only 7–34%; Al-Husary does better (70.5%). Separate
  entries per style remain necessary.
- **Mujawwad** is named less often: 77.3% clean, 50.0% phone-like.
- **Weakest reciter**: `qatami`, named correctly in 52.3% of clips.
- **Most frequent confusion**: `juhany` named as `sowaid` (6 clips).
- **Imitators, very old recordings, mosque echo**: not measured. An imitator
  close enough to the original will be named as the original.

### What these numbers do not show

1. **Gallery and test clips come from the same recorded mushaf** for each
   reciter (different ayahs, same microphone and room). Another recording of
   the same reciter will score lower. Not tested.
2. **The gallery's phone-like copies use the same simulation as the
   phone-like test clips.** The phone-like figures are the most optimistic.
3. **Strangers were other famous studio reciters**, not amateurs or imitators.
4. **Choices were tuned on the same 26 reciters** over two rounds (model,
   projection, calibration limit). Two-fold testing protects the threshold,
   not those choices, so expect somewhat lower numbers on new reciters.

### Decisions

- **Embedding model: WeSpeaker ResNet34-LM, not the brief's ECAPA-TDNN.**
  At the same false-accept rate it named 77.4% correctly against 71.7%, and it
  is smaller (27 MB against 83 MB) and faster (170 ms against 267 ms). License
  CC BY 4.0, so the apps must credit the WeSpeaker project.
- **LDA projection fitted on the gallery itself** at load time; worth about
  5 more points. Not a trained model: recomputed in milliseconds whenever the
  gallery changes.
- **ONNX Runtime + NumPy features**, no PyTorch in the service.
- **Decision rule: threshold and margin** — `RECITER_THRESHOLD=0.725`,
  `RECITER_MIN_MARGIN=0.12`. The margin is a setting the brief does not have.
- **Gallery stores a phone-like copy of every clip** next to the studio one.
- **Scoring in memory, Postgres as the store.**
- **`country` is null for every reciter.** No source here provides it and it
  was not guessed.
- Tried and rejected: score normalization (z-, t-, s-norm), per-length
  calibration, extra short gallery windows. Numbers in the plan.

### Environment change made with approval

`www.mp3quran.net` added to the `ansit` cloud environment.

### Open issues

1. **17% of known reciters still come back as unknown** (26% on phone-like
   audio, 24% on 5 s clips). The reliable lever left is more audio per
   request; loosening the threshold trades directly against false accepts.
2. **No second recording per reciter**, so robustness to a different
   recording is unknown. This is the biggest gap for real use.
3. **Attribution owed in the apps**: WeSpeaker (CC BY 4.0) and Tanzil.
4. **Reciter `country` is empty** (the reciter screen shows it).
5. mp3quran full-surah URLs are stored but have not been fetched.
6. The speaker-model tests that need the ONNX file do not run in CI.
7. Carried over: no non-Quran speech negatives; EveryAyah audio has no stated
   license; Flutter not installed here.

### Next

Phase 4 — done, see below.

## Phase 4 — production API · complete, awaiting review

Plan and decisions: [`plans/phase-4.md`](plans/phase-4.md) ·
API reference: [`API.md`](API.md)

### What was built

- `POST /v1/identify`: both branches (ASR → ayah match, speaker embedding →
  reciter decision) run at the same time on one decoded waveform and are fused
  into the response schema from the brief.
- `GET /v1/surahs`, `/v1/surahs/{n}`, `/v1/ayahs/{surah}/{ayah}?context=N`,
  `GET /v1/reciters`, `/v1/reciters/{id}`, `POST /v1/feedback`.
- Startup loading as readiness tasks: `/readyz` shows `quran_index`,
  `asr_model`, `speaker_model`, `reciter_gallery` individually.
- Rate limiting per IP and per `X-Device-ID` (Redis; in-process without it),
  upload and duration limits, CORS allowlist, one error format.
- "Listen longer": `previous_identify_id` resolves an ambiguous result using
  only the earlier candidates' positions (kept 5 minutes).
- Metrics: per-stage latency, outcome counts, confidence and similarity
  histograms. Tables `identify_events` and `feedback` (migration `0002`).
- Docker: CPU image with models mounted (default) or baked (`--target baked`),
  migrations at container start, read-only filesystem. GPU Dockerfile provided.
- `infra/locust/locustfile.py` load test; `make serve | gallery-db | loadtest`.
- 54 new tests (210 total).

### Verified by running it

- **Real clip through HTTP**: a 12 s phone-like clip of Al-Afasy returned the
  right surah and ayah and named the reciter (also an automated test, run
  where the models exist).
- **Docker stack** (`postgres + redis + backend`): migrations applied at start;
  gallery loaded from Postgres after `make gallery-db`; an identify request
  wrote one `identify_events` row; feedback stored; the 21st request in a
  minute got 429 with counters visible in Redis; container runs as uid 10001
  on a read-only filesystem and `/tmp` stayed empty.
- **Privacy**: tests assert that no file is created during a request
  (including a 1.7 MB upload), that the log line for a request contains no
  transcript, and that `identify_events` has no column or value holding one.

### Load test (Locust, this 4-vCPU machine, client on the same host)

Final defaults: 2 requests at once, each with 2 ASR threads + 1 speaker
thread. Mixed 5 / 8 / 12 s phone-like clips, users send back to back, 75 s
per run, no failures in any run.

| Concurrent users | Requests/s | p50    | p95   | p99   |
| ---------------- | ---------- | ------ | ----- | ----- |
| 1                | 1.18       | 0.87 s | 1.1 s | 1.2 s |
| 2                | 1.80       | 1.1 s  | 1.6 s | 1.8 s |
| 4                | 1.77       | 2.3 s  | 2.8 s | 2.9 s |

For comparison, the first configuration tried (1 request at a time, 3 ASR
threads): p95 1.6 s / 3.4 s / 6.6 s at 1 / 2 / 4 users, about 0.9 requests/s.

- **One instance on 4 vCPU handles about 1.8 identifications per second.**
  The brief's 2.5 s p95 budget holds up to 2 concurrent users and is exceeded
  at 4 (2.8 s), where requests wait for a free slot. More load needs more
  instances; the API is stateless apart from Redis and Postgres.
- These runs used the server started directly with `uvicorn`, without
  Postgres or Redis. The Docker stack was exercised functionally, not under
  load.
- The load generator shared the 4 cores with the server, so real capacity is
  somewhat higher than measured.

### Decisions

- **No temp files at all** instead of "temp files on tmpfs removed in
  `finally`": the clip is decoded from memory. Stronger than the brief asks.
- **"Listen longer" stores candidate positions, not the transcript.**
- **Thread counts set by measurement**: 2 ASR threads beat 3 and 4.
- **Gallery from Postgres when it holds one, otherwise from files**, so the
  service also runs without Postgres or Redis (`make serve`).
- **Rate limiter uses a per-process fallback** if Redis is configured but unreachable; global enforcement is degraded until Redis recovers.
- **`X-Forwarded-For` is ignored unless `TRUST_PROXY_HEADERS=true`.**
- **Unknown reciter returns best guesses as `alternatives`** but no name.
- **Locust instead of k6** (k6 is not available here; the brief allows either).

### Open issues

1. **Capacity is ~1.8 requests/s per 4-vCPU instance.** Fine for a launch,
   but worth knowing before any promotion.
2. **Deployment needs `TRUST_PROXY_HEADERS=true` behind a reverse proxy**,
   otherwise every user shares the proxy's IP and one rate limit.
3. **The GPU Dockerfile is untested** (no GPU here). Marked as such in the file.
4. **Full-surah audio links are not returned**: the mp3quran URL pattern has
   not been fetched and checked. Per-ayah EveryAyah links are returned.
5. **Hot-linking EveryAyah audio from the apps** is a product and licensing
   decision; the site states no terms.
6. **Image is 948 MB** before models.
7. Model-dependent tests still run only locally, not in CI.
8. Carried over: no non-Quran speech negatives; no second recording per
   reciter; reciter `country` empty; attribution owed in the apps (Tanzil,
   WeSpeaker); Flutter not installed here.

## Phase 5 — Web app

Plan: [`docs/plans/phase-5.md`](plans/phase-5.md). App: [`web/`](../web/README.md).

### What exists

- Next.js 16 / React 19 / Tailwind 4 app, Arabic and RTL, dark + light themes.
- Screens: home, listen (permission explainer, recording, identifying),
  result, ambiguous result, history / saved, reciter, settings, and a
  "coming soon" mushaf tab; all error and empty states.
- Local history in IndexedDB (results only), per-ayah audio player with
  auto-advance, feedback sheet, share, PWA manifest + icons + service worker.

### Checks (run on 2026-11-17)

| Check                      | Result                          |
| -------------------------- | ------------------------------- |
| `npm run lint`             | clean                           |
| `npm run typecheck`        | clean                           |
| `npm test` (Vitest)        | 20 passed                       |
| `npm run e2e` (Playwright) | 6 passed (API mocked, fake mic) |
| `npm run build`            | succeeds, all routes static     |

Real end-to-end check, done by hand once: a 12 s studio clip of Yusuf 84 was
played into Chromium as the microphone, with the web app pointed at the real
backend. Result page showed the right surah and ayah (text match 100%), the
reciter as "unknown" with the correct reciter as first guess (69%). Upload to
result page took 1.2 s and 1.9 s in two runs. Playback of per-ayah audio from
the reciter page worked.

### Not verified

- **No real phone or real microphone was used.** Safari / iOS recording
  (`audio/mp4`) is handled in code but untested.
- The service worker and "install as app" were not exercised in a browser;
  they only register in production builds.
- No screen-reader pass and no automated accessibility audit.
- The permission explainer is covered by the manual run, not by the e2e tests
  (Chromium's fake-microphone flag reports permission as already granted in
  that setup).

### Open issues

1. **No Dockerfile for the web app yet**, and it is not in `docker-compose`.
2. **The home-screen motto is the one piece of Quran text typed in the code**
   (in `messages/ar.json`), copied from the approved mockup. Everything else
   comes from the API. Needs an explicit yes/no from the owner.
3. Favourite reciters are stored locally but not listed anywhere yet.
4. Tafsir is a disabled "soon" button; the mushaf tab is a placeholder.
5. Listening needs HTTPS (or localhost): a browser rule, relevant to deploys.
6. "Continue listening" with an unknown reciter falls back to a fixed default
   reciter (`alafasy`) if there is no guess.

## Phase 6 — Mobile app

Plan: [`docs/plans/phase-6.md`](plans/phase-6.md). App: [`mobile/`](../mobile/README.md).

### What exists

- Flutter 3.50 app (Android + iOS projects) with the brief's stack: Riverpod,
  go_router, dio, `record`, `permission_handler`, `just_audio`, drift.
- The same screens, copy and tokens as the web app. Arabic strings are
  generated from the web app's `messages/ar.json` (179 strings).
- Permission flow: in-app explainer first, then the system dialog; a refusal
  can be retried; a permanent refusal links to the app's settings.
- Recording goes from the microphone to memory to the upload; no audio file
  is created on the device.
- Haptics on start / stop / result; animations stop under reduce-motion.
- Local history in SQLite (drift); per-ayah playback with auto-advance.

### Checks (run on 2026-11-17)

| Check             | Result                                                                                                                 |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `flutter analyze` | no issues                                                                                                              |
| `flutter test`    | 55 passed: 41 widget tests (screen states and the record → upload → result flow), 14 unit tests incl. the SQLite store |

The screens were also rendered to images with the real fonts through the test
runner and compared by eye with the web app: home, permission explainer,
listening, result (identified and unknown reciter), ambiguous result, history,
reciter and settings all lay out correctly at 402 × 874.

Two real bugs were found by the tests and fixed: the Stop button stayed
disabled at exactly 3.0 s because of a floating-point sum, and a provider was
read during `dispose`.

### Not verified — important

- **The app has never run on a phone or an emulator.** This environment cannot
  reach the Android SDK and has no macOS. Everything that only exists on a
  device is therefore untested: real recording (`record` PCM stream), the
  system permission dialog, real audio playback, haptics, SQLite on device.
- **The iOS project has never been built.** `permission_handler` needs
  `PERMISSION_MICROPHONE=1` in the iOS `Podfile`, which Flutter only creates on
  the first build on a Mac. Until that is added, the iOS permission request
  will not work.
- The `integration_test` flow exists but has not been run on a device.
- The APK built by CI has not been installed by anyone yet.

### Decisions

- **PCM stream to in-memory WAV instead of AAC/Opus files** (a deviation from
  the brief's suggested formats): no audio ever touches the phone's storage.
  About 320 KB per 10 s clip against the 2 MB limit.
- **iOS microphone text is one string holding Arabic and English**, not two
  localised `InfoPlist.strings`, because adding localisations to an Xcode
  project by hand cannot be checked here.
- **Debug builds allow plain http** (Android cleartext, iOS local networking)
  and show a server-address field in Settings; release builds do neither.

### Open issues

1. Run on real Android and iOS devices; fix whatever that shows.
2. iOS: add the `Podfile` permission macro on a Mac; split the microphone text
   into proper Arabic / English localisations.
3. No app icon or splash screen yet (Flutter defaults).
4. Release signing, store listings and privacy labels are not started.
5. Carried over from Phase 5: the home-screen motto needs the owner's yes/no;
   favourites are stored but not listed; tafsir and mushaf are placeholders;
   no Dockerfile for the web app.

## After Phase 6 — changes from the owner's first trial (2026-11-17)

The owner ran the backend and the web app on Windows. Ayah identification
worked; reciter accuracy was judged "very reasonable" once the gallery files
were in place.

- **Reciter recognition silently off.** Without `resnet34.onnx` and
  `gallery.npz` the server returns no reciter. The apps showed that as "not
  sure of the voice" with an empty reciter list. They now say recognition is
  unavailable. README explains the `/readyz` check.
- **Three reciters added on request**: Ahmad Talib bin Humaid, Mohammed
  Al-Lohaidan, Haitham Aldukhain. EveryAyah does not have them, so the gallery
  builder gained a second source: 10-second windows from six of mp3quran's
  full-surah files per reciter. Gallery: 38 reciters, 42 voices, 5,030 clips.
- Check on surahs the gallery never saw (36 and 67; 24 clips of 8 s per
  reciter and condition; `ml/eval/added_reciters_check.py`), at the service's
  settings (0.725 / 0.12):

  | Reciter     | Clean: named right | Phone-like: named right | Named wrong | As a stranger: wrongly named |
  | ----------- | ------------------ | ----------------------- | ----------- | ---------------------------- |
  | ahmad-talib | 24 / 24            | 20 / 24                 | 0           | 0 / 48                       |
  | luhaidan    | 24 / 24            | 22 / 24                 | 0           | 1 / 48                       |
  | dukhain     | 24 / 24            | 14 / 24                 | 0           | 0 / 48                       |

  **Caveat:** queries and gallery come from the same recording series, so
  these are optimistic. A different recording of the same reciter is untested.

- The 35 earlier reciters, re-measured with the larger gallery at the same
  settings: 2.9% false accepts, 81.5% identified, 0.6% misidentified, 17.9%
  unknown (before: 4.1% / 82.5% / 0.5% / 17.0%). Re-calibration would now
  pick margin 0 (3.5% / 83.8%); the settings were left as they are.
  `ml/eval/reports/phase3.md` now states the service's settings separately
  from the calibration optimum.
- **Limitation:** the three new reciters have no per-ayah audio. "Continue
  listening" and the reciter page say so instead of playing. Playing
  mp3quran's full-surah files is possible but not built.
- Tests now: backend 198 passed (12 need models, skipped in CI), web 20 unit +
  7 browser, mobile 58.

### Next

Phase 7 is optional in the brief (audio-fingerprint fast path, feedback
report) and should wait for real-device results and real usage data.

## Phase 8 — Tafsir and reciter library · in progress

- Added lazy per-ayah Tafsir al-Muyassar retrieval from QuranEnc, with source
  details and attribution in the result and Mushaf screens.
- QuranEnc's public endpoint does not expose an edition version for this
  translation. The UI discloses that fact; the source's reuse terms request
  the edition version, so publishing the translation remains subject to
  resolving that metadata gap.
- Reworked the reciter library into one searchable list, with no country tabs,
  and removed the duplicate library link from the landing navigation.
- Added Kamil Yusuf Al-Bahtimi, Al-Shahat Muhammad Anwar, and prominent older
  Egyptian reciters, plus listed imams from both Harams. The Haramain names
  follow the Presidency roster (including Al-Waleed bin Khalid Al-Shamsan).
- Added source portraits and source credits where portraits were verified;
  missing images use a neutral Quran-book icon, never initials.
- Verified direct MP3Quran surah files for entries that have them. Records with
  no verified audio remain directory entries and do not become enabled for
  reciter recognition. Kamil and Al-Shahat link to their available SoundCloud
  recordings; these are not used as recognition data.
- The landing-library link fix and list changes pass web type-check, ESLint,
  and the browser regression for search, the requested names, and a single
  landing navigation link.
- Remaining: source/license confirmation for the tafsir edition version, verify
  portrait links on more devices, and gather/reference additional audio where
  currently absent.

## Redesign, reciter profiles and PWA (2026-11-22)

Branch `redesign/identity-profiles-pwa`, on top of `hardening/production-readiness`.

### What changed

- **Recording minimum is 5 s on web and mobile.** The web button reads
  "cancel" until then and "stop" after, so a recording is never discarded
  silently (that had broken six browser tests).
- **New visual identity** ("the manuscript"): paper, ink, lapis blue and
  rubrication red; Reem Kufi headings, Readex Pro interface text, Amiri Quran
  for ayahs only; squared corners and hairline rules. Light is now the
  default; dark follows the system or the setting.
- **Shared top navigation on wide screens**, bottom bar on phones. App screens
  use a readable column or the full shell instead of a phone-width column.
- **Landing page rebuilt.** Its verse (7:204) is now copied from the Tanzil
  Uthmani file by `web/scripts/make-verses.mjs`, not typed by hand.
- **Reciter profiles**: `/reciters/<id>` for all 64 reciters (55 in the
  registry, 9 directory-only), a library with Arabic/English search and five
  category filters. Content is in `web/src/data/reciter-profiles.json`.
- **API (additive):** `recognition_enabled` on reciter summaries (true only if
  the voice gallery holds the reciter) and `surah_audio` on reciter details.
  The player can now play full-surah recordings, so the mp3quran-only reciters
  are playable.
- **PWA:** manifest (name ANSIT, short name أنصت), new icons, a versioned
  service worker, an install button (Chromium prompt; Add-to-Home-Screen
  instructions on iOS Safari), an offline page, and an update prompt.

### Checks run on this branch

| Check                       | Result                                      |
| --------------------------- | ------------------------------------------- |
| Backend: ruff, mypy, pytest | clean; 204 passed, 12 skipped (need models) |
| Web: ESLint, tsc            | clean                                       |
| Web: Vitest                 | 28 passed                                   |
| Web: Playwright             | 18 passed                                   |
| Web: production build       | 77 static pages                             |
| Mobile: analyze, tests      | clean; 58 passed                            |

Browser verification against the production build (Chromium):

- `Page.getInstallabilityErrors`: none. Manifest parse errors: none.
- Service worker registered and controlling the page; offline, a visited
  profile opened from cache, an unvisited one showed the offline page, and
  `/history` opened from the precache.
- Update flow: registering a worker for a new build showed the prompt;
  accepting it reloaded onto the new worker.
- No horizontal overflow on 11 routes at 375, 390, 430, 768, 1024 and 1440 px.
- One real identification through the new UI against the real backend
  (12 s studio clip of 12:84): correct surah and ayah.

### Not verified

- **Installing on a real phone or desktop** (the install prompt itself, iOS
  Add to Home Screen, the standalone window). Headless Chromium reports the
  site installable but does not fire the prompt.
- **Portraits did not load here**: this environment blocks the image hosts,
  so every screenshot showed the initials fallback. They need a look on a
  normal connection.
- No screen-reader pass; no Lighthouse run.

### Biography data: how far to trust it

- 59 of 64 reciters have a sourced short biography; 33 of them a fuller one.
  Five have nothing because no reliable source was found (alaqmi, dukhain,
  ahmad-kaseb, muhammad-dibirov, omar-diaa-al-din).
- **All facts were taken from web-search result summaries, not from pages
  opened and read**: Wikipedia could not be reached from this environment.
  Each profile lists its sources, conflicting dates were left out, and only
  entries rated high-confidence got dates and full text. A human read-through
  against the listed sources is still needed before launch.
- A unit test fails if any profile states a fact without a source.

### Open issues

1. **`hudhaify` and `ali-hudhaifi` are the same person** (Ali Al-Hudhaify),
   entered twice in the registry. Two voice identities for one reciter will
   hurt recognition of him. One should be removed after checking the gallery.
2. **Portraits are hot-linked from news and social sites**; only the Wikimedia
   ones have a clear licence. Unchanged from before, still unresolved.
3. Registry has 55 reciters; the gallery built here has 38. Reciters without a
   gallery voice now show "not supported" instead of implying recognition.
4. The gallery builder on this branch builds weaker voices for mp3quran-only
   reciters (48 clips, fewer phone-like copies) than the one measured earlier.
5. The mobile app still has the old look (green/gold, old fonts) and no
   profiles; it shares only the 5 s minimum and the strings.
6. After an update, one old cache can survive until the next activation.
7. Tafsir edition-version and rate-limit gaps noted earlier still stand.
