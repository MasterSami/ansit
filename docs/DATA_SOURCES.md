# Data sources

Each source is checked by actually inspecting it (sample, schema, license) in
the phase that first uses it. Findings are recorded here.

| Need                            | Source                                                              | Verified in | Status       |
| ------------------------------- | ------------------------------------------------------------------- | ----------- | ------------ |
| Quran text for matching         | Tanzil "simple clean"                                               | Phase 1     | **verified** |
| Quran text for display          | Tanzil Uthmani                                                      | Phase 1     | **verified** |
| Surah / juz / page metadata     | Tanzil `quran-data.xml`                                             | Phase 1     | **verified** |
| Per-ayah recitation audio       | EveryAyah (HF `tarteel-ai/everyayah`)                               | Phase 2     | not verified |
| Reciter names, full-surah audio | mp3quran API, Quran Foundation API                                  | Phase 3     | not verified |
| ASR model                       | `tarteel-ai/whisper-base-ar-quran` + one larger Quran-tuned Whisper | Phase 2     | not verified |
| Speaker embedding model         | `speechbrain/spkrec-ecapa-voxceleb`                                 | Phase 3     | not verified |

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

## For the remaining sources

Record: exact URL or dataset id, file format and schema, license and
attribution terms, and anything that differs from the build brief.
