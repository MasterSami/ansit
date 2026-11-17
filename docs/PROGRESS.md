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

Plan and decisions: [`plans/phase-3.md`](plans/phase-3.md) ·
Full report: [`../ml/eval/reports/phase3.md`](../ml/eval/reports/phase3.md)

### What was built

- `app/speaker/` — NumPy filterbank features, ECAPA-TDNN on ONNX Runtime
  behind a `SpeakerEngine` interface, an in-memory gallery with scoring and
  the open-set decision, and persistence in Postgres.
- `app/db/` — tables `reciters`, `gallery_clips`, `reciter_centroids` with
  `vector(192)` columns, and the first Alembic migration.
- `ml/registry/reciters.json` — 35 reciters, 39 voices (reciter × style),
  names from the mp3quran API.
- `ml/scripts/` — `export_speaker_model.py`, `build_registry.py`,
  `build_gallery.py`, `load_gallery_db.py`. Adding a reciter is
  `make gallery RECITER=id`; nothing is retrained.
- `ml/eval/reciter_eval.py` and its report.
- 31 new tests (151 total), including persistence tests against a real
  Postgres with pgvector, which CI now runs as a service.

Still a library; both branches are joined into one request in Phase 4.

### Results

| Target                                       | Result                                         | Verdict |
| -------------------------------------------- | ---------------------------------------------- | ------- |
| False accept ≤ 5% on out-of-gallery reciters | 3.2% (two-fold, 1,232 test clips, 26 reciters) | met     |

At that setting, for a reciter who is in the gallery:

|                       | All clips | Clean | Phone-like |
| --------------------- | --------- | ----- | ---------- |
| Named correctly       | 71.8%     | 79.2% | 64.4%      |
| Named as someone else | 0.5%      | 0.6%  | 0.3%       |
| Returned as unknown   | 27.7%     | 20.1% | 35.2%      |

- Closed-set Top-1 (no rejection): 93.0%. EER: 6.57% (5.19% clean, 7.30%
  phone-like).
- Longer clips help: 60.7% named correctly at 5 s, 68.1% at 8 s, 83.9% at 12 s.
- Embedding time: 267 ms p50 on an 8 s clip with 4 threads.
- The model runs on ONNX Runtime; parity with SpeechBrain is cosine 1.000000.
  **The service still needs no PyTorch.**

### Hard cases, documented honestly

- **Same reciter, different style.** Abdul Basit and Al-Minshawi in a style
  the gallery lacks are named correctly in only 0–2% of clips (ranked first
  in 14–64%). Murattal and mujawwad are close to two different voices for
  this model. Separate centroids per style are therefore necessary, and a
  reciter is only recognised in styles the gallery holds. Al-Husary's
  murattal against his other two styles does much better (79.5%).
- **Mujawwad overall** is named less often: 43.2% clean, 40.9% phone-like.
- **Weakest reciters**: `jibreel` 29.5% and `qatami` 38.6% named correctly;
  their own-voice scores sit close to the threshold.
- **Most frequent confusion**: `rifai` named as `abdul-basit` (8 clips).
- **Imitators, very old recordings, mosque echo**: not measured. An imitator
  close enough to the original will be named as the original.

### What these numbers do not show

1. **Gallery and test clips come from the same recorded mushaf** for each
   reciter (different ayahs, same microphone and room). Another recording of
   the same reciter will score lower. Not tested: there is no second
   recording per reciter here.
2. **The gallery's phone-like copies use the same simulation as the
   phone-like test clips.** The phone-like figures are the most optimistic
   ones in the report.
3. **Strangers were other famous studio reciters**, not amateurs or imitators.
4. The calibration limit (3%) was chosen after seeing test results; see the
   plan.

### Decisions

- **ONNX Runtime + NumPy features instead of PyTorch** in the service.
- **Decision rule is threshold _and_ margin** — `RECITER_THRESHOLD=0.60`,
  `RECITER_MIN_MARGIN=0.08`. The margin is a new setting, not in the brief.
  With the brief's threshold-only rule the same false-accept target gave
  55.4% named correctly instead of 71.8%.
- **Gallery stores a phone-like copy of every clip** next to the studio one.
- **Scoring in memory, Postgres as the store.** pgvector columns are in place.
- **`country` is null for every reciter.** No source here provides it and it
  was not guessed. It needs filling in by hand or from another source.
- Score keeps the brief's equal mix of centroid and top-5 clips; the three
  variants are within 1.8 points of each other on Top-1.

### Environment change made with approval

`www.mp3quran.net` added to the `ansit` cloud environment.

### Open issues

1. **About 28% of known reciters come back as unknown** at this false-accept
   rate (35% on phone-like audio). Loosening the setting names more reciters
   and accepts more strangers; the curves are in the report.
2. **No second recording per reciter**, so robustness to a different
   recording is unknown. This is the biggest gap for real use.
3. **Reciter `country` is empty** (the reciter screen shows it).
4. mp3quran full-surah URLs are stored but have not been fetched; verified
   when "continue listening" is built.
5. The speaker-model tests that need the ONNX file do not run in CI.
6. Carried over: no non-Quran speech negatives; EveryAyah audio has no stated
   license; Flutter not installed here; Tanzil attribution due in the UI.

### Next

Phase 4 — production API. Not started; waiting for review.
