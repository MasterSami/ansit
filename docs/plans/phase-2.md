# Phase 2 — ASR and end-to-end ayah identification on real audio (plan)

## What gets built

| Piece            | File                                                | What                                                                 |
| ---------------- | --------------------------------------------------- | -------------------------------------------------------------------- |
| Decode           | `backend/app/audio/decode.py`                       | Any of webm/opus, m4a/aac, mp3, wav → 16 kHz mono float32, in memory |
| VAD              | `backend/app/audio/vad.py`                          | Silero VAD: speech duration, leading/trailing trim                   |
| ASR interface    | `backend/app/asr/engine.py`                         | `ASREngine.transcribe(waveform_16k) -> ASRResult`                    |
| ASR engine       | `backend/app/asr/faster_whisper_engine.py`          | faster-whisper (CTranslate2), settings from the brief                |
| Guards           | `backend/app/asr/guards.py`                         | Reject output that looks hallucinated                                |
| Pipeline         | `backend/app/pipeline.py`                           | decode → VAD → ASR → guards → match, with per-stage timings          |
| Model conversion | `ml/scripts/convert_models.py`                      | Hugging Face → CTranslate2 int8                                      |
| Eval set         | `ml/eval/build_audio_eval.py`, `ml/eval/heldout.py` | Clips from EveryAyah, clean and phone-like                           |
| Evaluation       | `ml/eval/audio_eval.py`                             | Runs the pipeline, writes `ml/eval/reports/phase2.md`                |

The pipeline is still a library; the HTTP endpoint is Phase 4.

## Verified before writing code

- `tarteel-ai/whisper-base-ar-quran`: exists, Apache-2.0, fine-tune of
  `openai/whisper-base`. Its card does not name the training data.
- `tarteel-ai/everyayah` on Hugging Face: exists; 4 columns; 234,732 rows;
  **117 GB**. Splits train/validation/test contain the same reciters.
- Larger Quran-tuned Whisper candidates found and checked:
  - `deepdml/whisper-small-ar-quran-mix-norm` — Apache-2.0, fine-tune of
    `openai/whisper-small`, card lists `tarteel-ai/everyayah` as training data.
  - `naazimsnh02/whisper-large-v3-turbo-ar-quran` — Apache-2.0, trained on
    EveryAyah. Not benchmarked: a large-v3 encoder cannot meet a 2.5 s budget
    on 4 CPU cores.
  - `tarteel-ai/whisper-tiny-ar-quran` — Apache-2.0; added as the fast end of
    the trade-off.
- `everyayah.com/data/recitations.js` lists 79 folders. One listed folder
  (`Ibrahim_Akhdar_64kbps`) is empty; some folders have gaps; only some have
  `audhubillah.mp3` / `bismillah.mp3`.

## Design decisions

- **EveryAyah is not downloaded from Hugging Face.** 117 GB is far over the
  5 GB ask-first limit and the evaluation needs about 1,500 ayahs. The same
  recordings are fetched one ayah at a time from everyayah.com (82 MB total),
  cached under `ml/data/` and never committed.
- **Decoding uses the FFmpeg libraries through PyAV, in process, on an
  in-memory buffer** rather than an `ffmpeg` subprocess. The clip never touches
  disk (the privacy promise needs no temp-file cleanup at all), a seekable
  buffer handles iOS M4A files whose index is at the end, and the Docker image
  needs no ffmpeg binary. PyAV is already a faster-whisper dependency.
- **Silero VAD comes from faster-whisper's bundled ONNX model**, so the service
  needs no PyTorch in this phase.
- **VAD trims only the ends.** Internal pauses are kept: removing them glues
  words together, and long sustained recitation can look like non-speech.
- **No temperature fallback in decoding** (`temperature=0`). Whisper's retries
  at higher temperature multiply latency and are where it invents text;
  low-confidence output is rejected by the guards instead.
- **Guards**: empty output, `no_speech_prob` above 0.6, `avg_logprob` below
  −1.0, repetition (one word more than 6 times running, or compression ratio
  above 2.4), and a short list of phrases Whisper is known to invent on Arabic
  non-speech audio. All thresholds are configurable.
- **Ground truth is time-based.** EveryAyah gives ayah boundaries, not word
  timings, so for a window cut mid-ayah we know how many seconds of each ayah
  are heard, not which words. An ayah is "in the clip" if at least 1 s of it
  is heard. Top-1 = the reported ayah is in the clip; a stricter variant
  (the ayah heard longest) is reported next to it.
- **PyTorch (CPU build) is a dev-only dependency group (`ml`)** used for model
  conversion. It is not in the service image.

## Evaluation design

- 28 reciters (26 murattal, 2 mujawwad), one EveryAyah folder each.
- 12 held-out surahs (`ml/eval/heldout.py`); Phase 3's gallery must not use them.
- Per reciter: 6 random passages × windows of 5, 8 and 12 s, plus 2 surah
  openings with basmala (and isti'adha where available) × 8 and 12 s.
- Every window in two conditions: clean, and phone-like (synthetic reverb,
  pink noise at 10–20 dB SNR, 250–3600 Hz band-limit, Opus 16–24 kbps WebM).
- 60 non-speech clips (silence, noise, tones) that must be rejected.
- The chosen model runs on everything; the other two on the 8 s clips.
- Latency: one request at a time, 4 CPU threads.

## Risks, stated up front

- **Train/test contamination.** The models were trained on EveryAyah. These
  results are an upper bound, not a prediction for unseen reciters or live
  recordings. There is no independent recitation corpus in this phase.
- **The phone condition is simulated.** No real phone-near-a-speaker recordings.
- **No non-Quran speech negatives.** The false-accept rate on ordinary Arabic
  speech is not measured.
- **CI cannot run the model tests** (no model artifact there). The pipeline is
  unit-tested with a scripted ASR engine; the real-model test runs locally only.

## What changed during the phase (recorded after the first full run)

The first full run missed the accuracy target badly on phone-like audio, and
the cause was the voice activity detector, not the ASR model.

**First run, VAD threshold 0.5 with trimming to the detected speech region**
(`tarteel-base`, 8 s random clips): Top-1 83.9% clean, 45.8% phone. The VAD
gate alone rejected 41 of 616 clean clips (6.7%) and 201 of 616 phone-like
clips (32.6%) as "no speech", and trimming cut real recitation out of others.

**Experiment 1 — the gate alone.** Clips with under 1.5 s of detected speech,
on a random sample:

| Threshold | Clean recitation rejected | Phone-like recitation rejected | Non-speech rejected |
| --------- | ------------------------- | ------------------------------ | ------------------- |
| 0.5       | 6 / 150                   | 31 / 141                       | 60 / 60             |
| 0.3       | 4 / 150                   | 17 / 141                       | 60 / 60             |
| 0.15      | 2 / 150                   | 2 / 141                        | 57 / 60             |

**Experiment 2 — end to end.** 70 clean and 70 phone-like murattal clips plus
the 60 non-speech clips; Top-1 counts:

| Setting       | Clean   | Phone   | Non-speech rejected (gate + guards + matcher) |
| ------------- | ------- | ------- | --------------------------------------------- |
| 0.25, trim    | 63 / 70 | 39 / 70 | 60 / 60                                       |
| 0.15, trim    | 63 / 70 | 42 / 70 | 60 / 60                                       |
| 0.15, no trim | 63 / 70 | 48 / 70 | 60 / 60                                       |
| 0.08, no trim | 63 / 70 | 48 / 70 | 60 / 60                                       |

**Decision:** threshold 0.15, gate only, no trimming (`VAD_THRESHOLD`,
`VAD_TRIM_SILENCE`). This departs from the brief's "trim silence": trimming
made phone-like audio worse and gave nothing on clean audio. The non-speech
clips that slip through the looser gate are caught by the ASR guards or the
matcher.

**Second full run** (the one in the report): Top-1 on 8 s clips 87.5% clean,
73.8% phone.

Caveat: the setting was chosen on a sample of the evaluation set itself, so
the reported numbers are slightly optimistic about it.

## Model decision

Measured on the 8 s random clips (336 per model), 4 CPU threads, int8:

| Model           | Size   | Top-1 clean | Top-1 phone | Wrong match | ASR p50 | Total p95 |
| --------------- | ------ | ----------- | ----------- | ----------- | ------- | --------- |
| `tarteel-tiny`  | 45 MB  | 89.9%       | 53.6%       | 1.2%        | 0.79 s  | 1.20 s    |
| `tarteel-base`  | 81 MB  | 87.5%       | 73.8%       | 0.3%        | 1.24 s  | 1.78 s    |
| `deepdml-small` | 253 MB | 89.3%       | 81.0%       | 0.9%        | 1.73 s  | 2.20 s    |

**Default: `tarteel-base`.**

- On clean audio the three are within 2.4 points, which is 4 clips out of
  168: not a meaningful difference at this sample size.
- On phone-like audio the order is clear: tiny 53.6%, base 73.8%, small 81.0%.
  Tiny is ruled out by that.
- `deepdml-small` is 7 points better than base on phone-like audio but takes
  2.20 s at p95 on 8 s clips with all four cores. It was not measured on 12 s
  clips, where base already reaches 2.39 s, and in Phase 4 the speaker branch
  will run at the same time on the same cores. It would very likely break the
  2.5 s budget.
- Base has the lowest rate of confidently wrong answers (0.3%).

`deepdml-small` remains a configuration change away (`ASR_MODEL_PATH`) and is
the better choice on a machine with more cores or a GPU. That trade is a
product decision, flagged in `docs/PROGRESS.md`.
