# Data sources

Each source is checked by actually inspecting it (sample, schema, license) in
the phase that first uses it. Findings are recorded here.

| Need                            | Source                                                                                                                                        | Verified in | Status       |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ------------ |
| Quran text for matching         | Tanzil "simple clean"                                                                                                                         | Phase 1     | **verified** |
| Quran text for display          | Tanzil Uthmani                                                                                                                                | Phase 1     | **verified** |
| Surah / juz / page metadata     | Tanzil `quran-data.xml`                                                                                                                       | Phase 1     | **verified** |
| Per-ayah recitation audio       | EveryAyah — fetched per ayah from everyayah.com, not the 117 GB HF dataset                                                                    | Phase 2     | **verified** |
| Reciter names, full-surah audio | mp3quran API v3 (Quran Foundation API not used)                                                                                               | Phase 3     | **verified** |
| ASR model                       | `tarteel-ai/whisper-base-ar-quran` (plus tiny and a small model for comparison)                                                               | Phase 2     | **verified** |
| Speaker embedding model         | `Wespeaker/wespeaker-voxceleb-resnet34-LM` (ONNX); the brief's `speechbrain/spkrec-ecapa-voxceleb` was verified and used first, then replaced | Phase 3     | **verified** |
| Arabic per-ayah tafsir          | QuranEnc `arabic_moyassar` (Al-Tafsir Al-Muyassar)                                                                                              | Phase 7     | Terms verified; version unresolved |

## QuranEnc Al-Tafsir Al-Muyassar (verified 2026-11-19)

- API: `https://quranenc.com/api/v1/translation/aya/arabic_moyassar/{surah}/{ayah}`.
- Live API verified 2026-11-19: the single-ayah response provides the requested
  coordinate and verbatim text but no edition version. The general translation
  list does not contain this tafsir key.
- Work: *Al-Tafsir Al-Muyassar* (التفسير الميسر), prepared by a group of scholars
  (نخبة من العلماء), King Fahd Complex for the Printing of the Holy Quran.
- QuranEnc explicitly permits downloading and republication if the text remains
  unmodified, publisher and source are credited, edition/version information is
  retained, corrections are reported, and new editions are adopted. The API
  returns one ayah by its surah and ayah coordinates; ANSIT validates the
  coordinates against its existing 114-surah Quran index before requesting it.
- The app loads a single requested ayah and caches it for six hours. It retains
  the provider text as received and links each display to its QuranEnc source
  page. **Open item:** QuranEnc's reuse terms require a version number, but its
  API does not publish one. Obtain the official edition number or written
  guidance from QuranEnc before treating republication as fully compliant.
- Primary terms and API documentation: https://quranenc.com/ar/home/api.
- Work/authoring attribution cross-check: https://qurancomplex.gov.sa/ (the
  complex's scholarly journal cites the work as prepared by a group of scholars).

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

## Speaker embedding model (verified 2026-11-17)

### In use: WeSpeaker ResNet34-LM

- `Wespeaker/wespeaker-voxceleb-resnet34-LM`, commit `f0c48c298f`, file
  `voxceleb_resnet34_LM.onnx` (27 MB, SHA-256 `7bb2f06e…ec068`, pinned in
  `ml/scripts/fetch_speaker_model.py`).
- **License: CC BY 4.0.** Attribution is required: credit the WeSpeaker
  project (https://github.com/wenet-e2e/wespeaker). **To do in the UI phases:**
  include this credit on the about / licenses screen.
- ResNet34 "r-vector", trained on VoxCeleb2 dev (5,994 speakers), large-margin
  fine-tuned; 256-dimensional output; 6.63 M parameters.
- Input features per its `config.yaml`: Kaldi `fbank`, 80 mel bins, 25 ms
  frames, 10 ms shift, then per-utterance mean subtraction.
- `app/speaker/features.py` reimplements those features in NumPy. The fetch
  script checks them against `torchaudio.compliance.kaldi.fbank`: embedding
  cosine similarity 1.000000 on four test signals; the model is rejected
  below 0.9999. The service needs ONNX Runtime only, not PyTorch.

### Verified and used first, then replaced: SpeechBrain ECAPA-TDNN

- `speechbrain/spkrec-ecapa-voxceleb`, commit `0f99f2d0eb`, Apache-2.0,
  192-dimensional, features `Fbank(n_mels=80)` + sentence mean normalization.
  It was exported to ONNX with exact parity and evaluated. The ResNet34 model
  named more reciters correctly at the same false-accept rate while being
  smaller and faster; the comparison is in `docs/plans/phase-3.md`.

## mp3quran API (verified 2026-11-17)

- `https://www.mp3quran.net/api/v3/reciters?language=ar` (and `language=eng`):
  244 reciters. Fields: `id`, `name`, `letter`, `date`, `moshaf[]`.
- Each `moshaf` (a recording): `name`, `rewaya_id` (1 = Hafs from Asim),
  `moshaf_type`, `server`, `surah_total`, `surah_list`.
- `moshaf_type` is `rewaya_id * 10 + kind`, with kind 1 = murattal,
  2 = mujawwad, 3 = muallim (checked against the Arabic labels for six
  reciters). Other kinds exist (a "special recitation", a dated recording) and
  are ignored.
- `server` is the base URL for full-surah audio: `<server><SSS>.mp3`.
  **Fetched and decoded on 2026-11-17** for three reciters (ids 107, 137, 273;
  surahs 13, 15, 25, 31, 32, 34, 36, 67) from `cdn.mp3quran.net`. A reciter
  may lack some surahs (404), as `surah_list` says.
- **No country field.** The registry's `country` is null for every reciter.
- No license or terms were found in the API responses.
- **Use of the audio:** for three reciters that EveryAyah does not have
  (Ahmad Talib bin Humaid, Mohammed Al-Lohaidan, Haitham Aldukhain), six
  full-surah files each were downloaded to build voice embeddings. As with
  EveryAyah, only embeddings are kept in the gallery; the audio stays in the
  local, uncommitted cache and is not redistributed. For Haitham Aldukhain the
  only Hafs recording is filed as kind 4 ("special recitation"); it is used
  and labelled murattal.

## Reciter registry

`ml/registry/reciters.json` (committed), built by `ml/scripts/build_registry.py`:
35 reciters, 39 voices. Names are copied from the mp3quran API. The mapping
from EveryAyah folders to mp3quran reciters is an explicit table in that
script, checked by eye against both sources.

Left out on purpose: folders that repeat a recording at another bitrate,
Warsh recitations, translations, and four folders with no confident mp3quran
match (Muhammad AbdulKareem, Aziz Alili, Karim Mansoori, Parhizgar) plus
Mustafa Ismail, whose EveryAyah recording style could not be confirmed.

## Fonts bundled in the mobile app (verified 2026-11-17)

| Font                 | Version | Licence (from the font file's own licence field) |
| -------------------- | ------- | ------------------------------------------------ |
| IBM Plex Sans Arabic | 1.101   | SIL Open Font License (scripts.sil.org/OFL)      |
| Amiri                | 1.002   | SIL Open Font License (openfontlicense.org)      |
| Amiri Quran          | 1.003   | SIL Open Font License (openfontlicense.org)      |

Downloaded as TTF from Google Fonts (`fonts.gstatic.com`) into
`mobile/assets/fonts/`. The web app loads the same families through
`next/font`. The OFL allows bundling and redistribution with the app.

## For the remaining sources

Record: exact URL or dataset id, file format and schema, license and
attribution terms, and anything that differs from the build brief.

## Reciter directory additions (2026-11-19)

- Names and per-surah MP3 server/availability: MP3Quran public v3 reciters API,
  documented at <https://www.mp3quran.net/eng/api>. Only entries whose Hafs
  moshaf lists the linked surah have an external listen action. These directory
  additions do not by themselves enable speaker recognition; that still
  requires an evaluated gallery profile.
- Haramain imam names: official Presidency list at
  <https://prh.gov.sa/ar/component/content/article?Itemid=440&id=226>.
- Photo portraits are remote embeds from the source page named on each curated
  library card. Image rights remain with those publishers/contributors; the
  app links back to the source and does not copy the images into the repository.
- Kamil Yusuf Al-Bahtimi portrait: Wikimedia Commons file page records the
  image as public domain in its source jurisdiction:
  <https://commons.wikimedia.org/wiki/File:Kamil_Yusuf_Al-Bahtimi.jpg>.
