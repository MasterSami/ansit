# Phase 3 — reciter identification, open-set (plan)

## What gets built

| Piece         | File                                                           | What                                                    |
| ------------- | -------------------------------------------------------------- | ------------------------------------------------------- |
| Features      | `backend/app/speaker/features.py`                              | 80-bin log-mel filterbank in NumPy                      |
| Engine        | `backend/app/speaker/engine.py`                                | `SpeakerEngine` interface; ECAPA-TDNN on ONNX Runtime   |
| Gallery       | `backend/app/speaker/gallery.py`                               | In-memory gallery, scoring, open-set decision           |
| Schema        | `backend/app/db/models.py`, `app/db/migrations/`               | Reciter registry, clip embeddings, centroids (pgvector) |
| Store         | `backend/app/speaker/store.py`                                 | Save / load registry and gallery in Postgres            |
| Model export  | `ml/scripts/export_speaker_model.py`                           | SpeechBrain → ONNX, with a parity check                 |
| Registry      | `ml/scripts/build_registry.py` → `ml/registry/reciters.json`   | 35 reciters                                             |
| Gallery build | `ml/scripts/build_gallery.py`, `ml/scripts/load_gallery_db.py` | Embeddings artifact, then into Postgres                 |
| Evaluation    | `ml/eval/reciter_eval.py`                                      | `ml/eval/reports/phase3.md`                             |

Still a library: wiring both branches into one request is Phase 4.

## Verified before writing code

- `speechbrain/spkrec-ecapa-voxceleb`: exists, Apache-2.0, ECAPA-TDNN with
  192-dimensional output, features = `Fbank(n_mels=80)` + sentence mean
  normalization. Pinned to commit `0f99f2d0eb`.
- mp3quran API (`/api/v3/reciters?language=ar|eng`): 244 reciters with Arabic
  and English names; each recording ("moshaf") has a riwaya id, a type code
  and a server URL for full-surah audio. No country field.
- EveryAyah folders encode reciter + style + bitrate, as the brief says. Several
  folders are the same recording at different bitrates; some reciters have two
  or three styles.

## Design decisions

- **The model runs on ONNX Runtime with NumPy features, not PyTorch.** ONNX
  Runtime is already installed (faster-whisper needs it), so the service gains
  no new heavy dependency and stays PyTorch-free. The export script refuses to
  write the model unless NumPy features + ONNX reproduce SpeechBrain's own
  embeddings; measured parity is cosine 1.000000. Measured speed on an 8 s
  clip, 4 threads: 244 ms against 710 ms for SpeechBrain on PyTorch.
- **A voice is a (reciter, style) pair**, each with its own centroid, as the
  brief suggests. A reciter's score is the best of their voices, so murattal
  and mujawwad do not blur each other.
- **Score = 0.5 × centroid cosine + 0.5 × mean of the top-5 clip cosines**
  (the brief's combination). The two components are compared in the report.
- **Postgres + pgvector is the store; scoring happens in memory.** The service
  loads the gallery at startup and scores it in NumPy. With about 2,300
  vectors that is far below a millisecond and removes the database from the
  request path. The vectors are still `vector(192)` columns, so pgvector
  queries work and an index can be added if the gallery grows a lot.
- **Registry names come from the mp3quran API**, never typed. The mapping from
  EveryAyah folders to mp3quran reciters is an explicit table in
  `build_registry.py`. **Country is left null**: no source here provides it,
  and it is not something to guess.
- **One folder per (reciter, style).** Duplicate-bitrate folders, Warsh,
  translations and folders without a confident mp3quran match are left out.
- **Gallery clips**: the same 60 ayahs for every voice, at most two per surah,
  10–22 words each, never from the 12 surahs held out for evaluation. Each
  clip is the middle 10 s of the ayah (about the length of a query).
- **Adding a reciter**: add them to the table, `make registry`,
  `make gallery RECITER=id`, `load_gallery_db.py --reciter id`. Nothing else
  is recomputed and nothing is retrained.
- **No reciter photos anywhere**; the registry has no image field.

## Evaluation design

- Queries: the 1,232 Phase 2 clips (28 folders = 26 reciters; held-out surahs;
  clean and phone-like; 5, 8 and 12 s).
- **Open-set by leave-one-reciter-out.** Every reciter is tested as a gallery
  member and, with their own entries ignored, as a stranger. That gives 26
  out-of-gallery reciters instead of a handful.
- **Threshold chosen on 13 reciters, reported on the other 13**: the lowest
  threshold giving at most 5% false accepts on calibration strangers.
- Reported: closed-set Top-1 and Top-3, EER, the accept/reject curve,
  clean vs phone-like, by clip length, by style, cross-style recognition,
  per-reciter results, most frequent confusions.

## Risks, stated up front

- **Same-recording bias.** A reciter's gallery clips and query clips are
  different ayahs of the same recorded mushaf. The embedding carries channel
  characteristics, so results are optimistic for another recording of the
  same reciter. There is no second recording per reciter in this phase.
- Out-of-gallery "strangers" are other famous studio reciters, not imitators
  or amateurs.
- The phone condition is simulated.

## What changed during the phase (recorded after the first evaluation)

**First run** — studio-only gallery, the brief's rule (`unknown` if the best
score is below a threshold), threshold from 13 reciters, measured on the other
13: false accept 3.6%, but only 54.5% of gallery members named (84.4% on clean
clips, **24.7% on phone-like clips**). Closed-set Top-1 was 90.2%.

The cause: reverb, noise and band-limiting lower _every_ similarity score, so
a threshold that keeps strangers out on clean audio rejects almost everyone on
degraded audio.

**Experiments** (single split, calibrated to 5% false accept on 13 reciters,
measured on the other 13):

| Gallery                                   | Decision rule       | Identified, clean | Identified, phone | False accept |
| ----------------------------------------- | ------------------- | ----------------- | ----------------- | ------------ |
| studio only                               | threshold           | 85.4%             | 25.6%             | 3.6%         |
| studio only                               | cohort z-score      | 82.5%             | 40.3%             | 3.9%         |
| studio only                               | lead over runner-up | 87.0%             | 46.4%             | 4.5%         |
| studio + phone-like copies (20 per voice) | threshold           | 83.8%             | 64.6%             | 7.8%         |
| studio + phone-like copies (20 per voice) | cohort z-score      | 82.5%             | 49.7%             | 5.0%         |
| studio + phone-like copies (20 per voice) | lead over runner-up | 86.7%             | 61.4%             | 5.7%         |

**Two changes adopted:**

1. **The gallery holds each clip twice**: the studio clip and a phone-like
   copy of it (reverb, noise, band-limit, Opus). 4,670 embeddings instead of
   2,335; the file grows from 1.7 MB to 3.3 MB.
2. **The decision needs a threshold _and_ a margin**: the best score must
   reach `RECITER_THRESHOLD` and lead the runner-up by `RECITER_MIN_MARGIN`.
   This adds one setting to the brief's list. A real match stands clear of the
   next reciter even when absolute scores are low.

**Calibration headroom.** A setting tuned to exactly 5% false accepts on 13
reciters gave 5.8% on the other 13. The setting is therefore calibrated to 3%,
which gave 3.2% on test reciters. This limit was chosen after seeing those
numbers; with 26 reciters there was no third group to keep blind.

**Final** (two-fold, every reciter is test data once): false accept 3.2%,
identified 71.8% (79.2% clean, 64.4% phone-like), misidentified 0.5%.
Shipped: `RECITER_THRESHOLD=0.60`, `RECITER_MIN_MARGIN=0.08`.

Caveat on the phone-like numbers: the copies in the gallery are made by the
same simulation as the phone-like test clips, so that gain is the most
optimistic figure in the report.
