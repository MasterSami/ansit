# Data sources

Each source is checked by actually inspecting it (sample, schema, license) in
the phase that first uses it. Findings are recorded here.

| Need                            | Source                                                                          | Verified in | Status       |
| ------------------------------- | ------------------------------------------------------------------------------- | ----------- | ------------ |
| Quran text for matching         | Tanzil "simple clean"                                                           | Phase 1     | **verified** |
| Quran text for display          | Tanzil Uthmani                                                                  | Phase 1     | **verified** |
| Surah / juz / page metadata     | Tanzil `quran-data.xml`                                                         | Phase 1     | **verified** |
| Per-ayah recitation audio       | EveryAyah — fetched per ayah from everyayah.com, not the 117 GB HF dataset      | Phase 2     | **verified** |
| Reciter names, full-surah audio | mp3quran API, Quran Foundation API                                              | Phase 3     | not verified |
| ASR model                       | `tarteel-ai/whisper-base-ar-quran` (plus tiny and a small model for comparison) | Phase 2     | **verified** |
| Speaker embedding model         | `speechbrain/spkrec-ecapa-voxceleb`                                             | Phase 3     | not verified |

## Tanzil (verified 2026-11-16)

Downloaded by `ml/scripts/download_quran.py` into `ml/data/tanzil/` (gitignored),
stored exactly as served.

| File                     | URL                                                                                         | Bytes     | SHA-256                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------ |
| `quran-simple-clean.txt` | `https://tanzil.net/pub/download/index.php?quranType=simple-clean&outType=txt-2&agree=true` | 781,176   | `228df2a717671aeb9d2ff573002bd28d6b3f973f4bc7153554e3a81663d67610` |
| `quran-uthmani.txt`      | `https://tanzil.net/pub/download/index.php?quranType=uthmani&outType=txt-2&agree=true`      | 1,370,878 | `bf4f57b968d03f4131c070b1e285da9be0e0a108a21c910e872801ca273312c8` |
| `quran-data.xml`         | `https://tanzil.net/res/text/metadata/quran-data.xml`                                       | 77,234    | `8867c1d88191472adec9db694b3cd9f135b1a2ef580574d32cf888dcb22c5c7a` |

### Format

- Text files: UTF-8, no BOM, one ayah per line as `surah|ayah|text`, 6,236
  lines, followed by a copyright block of `#` lines. Both report
  "Version 1.1".
- Simple-clean uses 36 Arabic letters plus space and nothing else. Uthmani
  uses 62 code points, including tashkeel, dagger alef (U+0670), alef wasla
  (U+0671), tatweel (U+0640) and Quranic annotation marks (U+06DC–U+06ED).
- `quran-data.xml`: 114 `sura` elements (`index`, `ayas`, `name`, `tname`,
  `ename`, `type` Meccan/Medinan, ...), 30 `juz`, 604 `page`, plus quarters,
  manzils, rukus and sajdas. Juz and pages are given as a starting
  `(sura, aya)`; the loader derives each ayah's juz and page from those.
- We use `tname` (e.g. "Al-Mulk") as the English surah name.

### Basmala

**Tanzil embeds the basmala at the start of ayah 1 of every surah except 1 and
9** (112 surahs), in both files. In the Uthmani file, surahs 95 and 97 spell
its first word with a shadda, so the prefix differs from 1:1 as a string.

The loader therefore splits the first four words off ayah 1 of those surahs,
after checking that they normalize to the words of 1:1, and fails if they do
not. The Uthmani prefix is kept verbatim in a separate field so it can be
displayed. A test rebuilds every Uthmani line from the two parts and compares
it with the file, so no display text is altered.

The isti'adha is not an ayah and does not appear in the files as a unit. Its
normalized words are assembled from word 2 of 113:1 and the last four words of
16:98.

### License and what it obliges us to do

Creative Commons Attribution 3.0, with these terms in the files:

- Verbatim copies only; **changing the text is not allowed**.
- The source (Tanzil Project) must be clearly indicated, with a link to
  tanzil.net.
- The copyright notice must be included in verbatim copies and "reproduced
  appropriately in all files derived from or containing substantial portion
  of this text".

How this is handled:

- The downloaded files are never edited and are not committed.
- The display text is the Uthmani text exactly as served (see Basmala above).
- The normalized text exists only inside the search index and is never shown.
- The index artifact carries the full copyright block in its `attribution`
  field, and the loader refuses a text file without that block.
- **To do in Phases 5 and 6:** the web and mobile apps must credit Tanzil
  Project and link to tanzil.net wherever ayah text is displayed.

## EveryAyah recitation audio (verified 2026-11-17)

### The Hugging Face dataset `tarteel-ai/everyayah`

- Exists. Splits `train` / `validation` / `test`; 234,732 rows; 4 columns
  (audio, duration, text, reciter).
- **117 GB** of parquet. Not downloaded: far over the 5 GB ask-first limit.
- The validation and test splits contain the same reciters as each other
  (15 listed in the dataset statistics), so the splits are not
  reciter-disjoint. Models trained on this dataset have heard these reciters.

### What we use instead: everyayah.com directly

The same recordings, one MP3 per ayah:
`https://everyayah.com/data/<folder>/<SSS><AAA>.mp3` (surah and ayah
zero-padded to three digits, e.g. `067001.mp3`).

- `https://everyayah.com/data/recitations.js` lists 79 folders with a display
  name and bitrate. Folder names encode reciter, style and bitrate
  (e.g. `Abdul_Basit_Mujawwad_128kbps`, `Husary_Muallim_128kbps`). The list
  also contains translations, Warsh recitations and teaching recordings.
- Not everything listed is there: `Ibrahim_Akhdar_64kbps` returns 404 for
  every file (the `_32kbps` folder works), and some folders have gaps.
- Some folders have `audhubillah.mp3` and `bismillah.mp3`; many do not. A
  basmala file `SSS000.mp3` exists for some surahs in some folders.
- Phase 2 downloaded 82 MB (about 1,500 ayahs from 28 folders) into
  `ml/data/everyayah/`.

### License

**No license or terms of use were found on everyayah.com.** Until that is
clarified, the audio is treated as not redistributable:

- cached locally under `ml/data/` (gitignored), never committed;
- no recitation audio in test fixtures (tests use synthetic audio);
- production stores embeddings only (Phase 3), never reciter audio.

## ASR models (verified 2026-11-17)

Converted to CTranslate2 int8 by `ml/scripts/convert_models.py`, which pins
each to the commit below and writes a `SOURCE.json` next to the model.

| Name            | Hugging Face repo                         | Commit       | License    | Base                   | Training data per its card                 |
| --------------- | ----------------------------------------- | ------------ | ---------- | ---------------------- | ------------------------------------------ |
| `tarteel-base`  | `tarteel-ai/whisper-base-ar-quran`        | `5c3c53fdf9` | Apache-2.0 | `openai/whisper-base`  | not stated                                 |
| `tarteel-tiny`  | `tarteel-ai/whisper-tiny-ar-quran`        | `c3d7e624af` | Apache-2.0 | `openai/whisper-tiny`  | not stated                                 |
| `deepdml-small` | `deepdml/whisper-small-ar-quran-mix-norm` | `2d0929ee4d` | Apache-2.0 | `openai/whisper-small` | `tarteel-ai/everyayah`, `tarteel-ai/EA-UD` |

- The Tarteel models write fully vowelled text in ordinary (imla'i) spelling,
  not Uthmani spelling, so it normalizes onto the simple-clean index directly.
  `deepdml-small` writes unvowelled text.
- When a basmala is recited before a surah, the Tarteel model usually leaves
  it out of the transcript.
- Also found, checked and not used:
  `naazimsnh02/whisper-large-v3-turbo-ar-quran` (Apache-2.0, trained on
  EveryAyah) — a large-v3 encoder is too slow for a 2.5 s budget on 4 CPU cores.
- Weight files are served from `us.aws.cdn.hf.co`.

Silero VAD is the ONNX model bundled inside the `faster-whisper` package
(MIT), so nothing extra is downloaded for it.

## For the remaining sources

Record: exact URL or dataset id, file format and schema, license and
attribution terms, and anything that differs from the build brief.
