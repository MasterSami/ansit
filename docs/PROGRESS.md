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

Phase 2 — ASR and end-to-end ayah identification on real audio. Not started;
waiting for review. It will need network access to Hugging Face for the models
and the EveryAyah dataset, and the dataset download size must be checked
against the 5 GB ask-first rule before anything is fetched.
