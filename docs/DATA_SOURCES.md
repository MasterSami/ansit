# Data sources

Nothing has been downloaded or verified yet. Each source below is checked by
actually inspecting it (sample, schema, license) in the phase that first uses
it, and the findings are recorded here.

| Need                            | Candidate source                                                    | Verified in | Status       |
| ------------------------------- | ------------------------------------------------------------------- | ----------- | ------------ |
| Quran text for matching         | Tanzil "simple clean"                                               | Phase 1     | not verified |
| Quran text for display          | Tanzil Uthmani                                                      | Phase 1     | not verified |
| Surah / juz / page metadata     | Tanzil quran-data                                                   | Phase 1     | not verified |
| Per-ayah recitation audio       | EveryAyah (HF `tarteel-ai/everyayah`)                               | Phase 2     | not verified |
| Reciter names, full-surah audio | mp3quran API, Quran Foundation API                                  | Phase 3     | not verified |
| ASR model                       | `tarteel-ai/whisper-base-ar-quran` + one larger Quran-tuned Whisper | Phase 2     | not verified |
| Speaker embedding model         | `speechbrain/spkrec-ecapa-voxceleb`                                 | Phase 3     | not verified |

For each one, record: exact URL or dataset id, file format and schema, license
and attribution terms, and anything that differs from the build brief.
