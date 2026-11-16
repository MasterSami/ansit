# Phase 1 — Quran text, normalization, ayah matcher (plan)

No audio in this phase. Input is text (what an ASR engine would produce), output
is a location in the mushaf.

## What gets built

| Step | File                                                        | What                                                                                                                          |
| ---- | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| 1a   | `ml/scripts/download_quran.py`                              | Fetches Tanzil simple-clean, Uthmani and `quran-data.xml` into `ml/data/tanzil/`, writes a manifest with SHA-256 of each file |
| 1a   | `backend/app/matcher/quran_data.py`                         | Parses the files, splits the embedded basmala off ayah 1, attaches juz/page, runs integrity assertions                        |
| 1b   | `backend/app/matcher/normalize.py`                          | `normalize_ar(text, level="search")` with a configurable standalone-hamza rule                                                |
| 1c   | `backend/app/matcher/index.py`, `ml/scripts/build_index.py` | Global word sequence, 1/2/3-gram postings, duplicate groups, artifact `ml/artifacts/quran_index.json.gz`                      |
| 1d   | `backend/app/matcher/search.py`                             | Offset voting → character-level alignment → span → ambiguity / no-match                                                       |
| 1e   | `ml/eval/text_eval.py`                                      | Synthetic-noise evaluation, hamza comparison, threshold calibration → `ml/eval/reports/phase1.md`                             |

## Findings from inspecting the real data (before writing code)

- Both text files: 6,236 lines, 114 surahs, format `surah|ayah|text`, then a
  copyright block of `#` lines. License: CC BY 3.0, verbatim copies only,
  attribution + link to tanzil.net, notice must travel with derived files.
- **The basmala is embedded in ayah 1 of 112 surahs** (all except 1 and 9).
  In the Uthmani file two of them (95 and 97) spell the first word with a
  shadda, so the prefix cannot be matched by string equality.
- Simple-clean uses only 36 letters + space. Uthmani uses 62 code points.
- `quran-data.xml`: 114 suras, 30 juz, 604 pages, each as a start `(sura, aya)`.
- The isti'adha is not an ayah, so it is not in the data as a unit.

## Design decisions

- **Basmala.** The loader removes the 4-word basmala prefix from ayah 1 of every
  surah except 1 and 9, comparing _normalized_ words against 1:1 and failing
  loudly on any mismatch. The Uthmani prefix is kept verbatim in a separate
  field (`basmala_uthmani`) so the UI can show it as a header. The Uthmani ayah
  text itself is never altered beyond that split.
- **Isti'adha without hand-typing.** Its normalized words are assembled from the
  data: word 2 of 113:1 plus the last four words of 16:98. An assertion checks
  that 113:1 and 114:1 agree on that word.
- **Prefix handling by variants.** If the query starts with something that looks
  like an isti'adha and/or basmala (fuzzy, to survive ASR noise), the matcher
  searches both the stripped and unstripped query and keeps the better score;
  ties go to the unstripped query. This keeps Al-Fatiha 1:1 matchable.
- **Standalone hamza.** Three settings are compared on data: `keep`, `drop`, and
  `merge_madd` (drop `ء` only when directly followed by alef, which is how the
  Uthmani script writes what simple script writes as `آ`). Chosen by: how often
  normalized Uthmani words equal normalized simple words, how many distinct
  words/ayahs collapse together, and matcher accuracy.
- **Artifact format.** gzip JSON, not pickle: safe to load, diffable, no
  Python-version coupling. It stores the normalized corpus, display text,
  metadata, duplicate groups and the normalization config. The n-gram postings
  are rebuilt in memory at load time; the load time is measured and reported.
- **Candidate generation.** Votes from 3-grams, 2-grams and rare single words,
  smoothed over ±2 word offsets to tolerate ASR merges/splits, top K = 20.
- **Scoring.** RapidFuzz `partial_ratio_alignment` of the joined query against a
  window of `len(query) ± 30%` words; the aligned character range is mapped back
  to words. Score is 0–100; `text_confidence = score / 100`.
- **Ambiguity.** Ambiguous when the matched span's exact word sequence occurs
  more than once in the Quran (this generalises whole-ayah duplicate groups to
  repeated phrases), or when a different location scores within
  `AMBIGUITY_DELTA`. `repeated_count` is the exact occurrence count.

## Evaluation design

- 2,000 spans, length uniform 4–25 words, start uniform over the global word
  sequence (so spans cross ayah and surah boundaries naturally). Fixed seed.
- Noise at nominal WER 0/5/10/15/20%: similar-letter substitutions, deletions,
  insertions, merges, splits. The realised edit rate is reported too.
- Ground truth "ambiguous" = the clean span's word sequence occurs more than
  once. Top-1/top-3 are reported on unique spans; ambiguous spans are scored on
  whether the true location is among the returned locations.
- Separate set: clips that start a surah with isti'adha and/or basmala prepended.
- Threshold calibration: scores of true spans vs. random word sequences drawn
  from the Quran's own vocabulary (hard negatives that share its words).

## Risks

- Synthetic noise is not real ASR noise. Thresholds from this phase are
  provisional and get re-calibrated on audio in Phase 2.
- The ASR model's output spelling (simple vs. Uthmani-like) is unknown until
  Phase 2; the hamza setting stays configurable for that reason.
- A basmala recited in the _middle_ of a clip (end of one surah into the next)
  is not removed. Measured in the eval, not fixed unless it matters.

## Done when

Unit tests pass, `ml/eval/reports/phase1.md` holds real numbers, PROGRESS.md is
updated. Then stop.
