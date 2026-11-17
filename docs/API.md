# API

Interactive docs: `http://localhost:8000/docs` (OpenAPI at `/openapi.json`).
The Swagger page can upload a file, which is the quickest way to try
`/v1/identify` by hand.

## Conventions

- Every response carries an `X-Request-ID` header. A client may send its own
  (`[A-Za-z0-9._-]`, up to 64 characters); anything else is replaced by a UUID.
- Errors always have this shape:

  ```json
  {
    "error": {
      "code": "audio_too_long",
      "message": "The audio clip is too long."
    }
  }
  ```

- Optional request headers:
  - `X-Device-ID` — a stable, client-generated id (8–64 characters of
    `[A-Za-z0-9._-]`). Used only for rate limiting. Not an account.
  - `X-App-Version` — recorded with identify events.
- Field names are stable. Fields may be added; none are renamed or removed.

## `POST /v1/identify`

`multipart/form-data`:

| Field                  | Required | Meaning                                                                                      |
| ---------------------- | -------- | -------------------------------------------------------------------------------------------- |
| `audio`                | yes      | 3–15 s of recitation. WebM/Opus, M4A/AAC, MP3 or WAV. At most 2 MB.                          |
| `client`               | no       | `web`, `ios` or `android`.                                                                   |
| `debug`                | no       | `true` to ask for debug output (see below).                                                  |
| `previous_identify_id` | no       | The `id` of an earlier **ambiguous** result that this clip continues from ("listen longer"). |

```bash
curl -F "audio=@clip.webm" -F client=web http://localhost:8000/v1/identify
```

### Response

```json
{
  "id": "92738cd4-030e-4975-a886-a856eeb642e6",
  "status": "match",
  "reason": null,
  "ayah": {
    "surah": 67,
    "surah_name_ar": "الملك",
    "surah_name_en": "Al-Mulk",
    "ayah": 1,
    "text_uthmani": "<Uthmani text from Tanzil, verbatim>",
    "juz": 29,
    "page": 562,
    "revelation": "meccan",
    "ayah_count": 30
  },
  "span": {
    "start": { "surah": 67, "ayah": 1, "word": 1 },
    "end": { "surah": 67, "ayah": 1, "word": 9 }
  },
  "text_confidence": 0.96,
  "candidates": [],
  "repeated_count": null,
  "reciter": {
    "status": "identified",
    "id": "minshawi",
    "name_ar": "محمد صديق المنشاوي",
    "name_en": "Mohammed Siddiq Al-Minshawi",
    "style": "murattal",
    "similarity": 0.86,
    "alternatives": [
      {
        "id": "husary",
        "name_ar": "محمود خليل الحصري",
        "name_en": "Mahmoud Khalil Al-Hussary",
        "style": "murattal",
        "similarity": 0.61
      }
    ]
  },
  "timings_ms": {
    "decode": 11,
    "vad": 25,
    "asr": 851,
    "match": 1,
    "speaker": 421,
    "total": 889
  }
}
```

Values above are illustrative.

| Field             | Meaning                                                                                                                                                                                                         |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `status`          | `match`, `ambiguous` or `no_match`.                                                                                                                                                                             |
| `reason`          | Only with `no_match`: `no_speech` (nothing that sounds like recitation), `too_short` (clip under 3 s, or too few words), `low_confidence` (heard something, could not place it).                                |
| `ayah`            | The ayah with the most matched words. Null with `no_match`.                                                                                                                                                     |
| `span`            | First and last matched word. A clip often covers more than one ayah.                                                                                                                                            |
| `text_confidence` | 0–1.                                                                                                                                                                                                            |
| `candidates`      | With `ambiguous`: up to 5 possible locations in mushaf order, each with `surah`, `surah_name_ar`, `ayah`, `score` and `context_before` (the preceding ayah's Uthmani text, null for the first ayah of a surah). |
| `repeated_count`  | With `ambiguous`: how many locations there are in total (may exceed 5).                                                                                                                                         |
| `reciter`         | Null with `no_match`. See below.                                                                                                                                                                                |
| `timings_ms`      | Per stage; `speaker` runs at the same time as `asr`, so `total` is not their sum.                                                                                                                               |
| `debug`           | Present **only** when the request sends `debug=true` **and** the server runs with `ALLOW_DEBUG=true`: `transcript_normalized`, `prefix_detected`.                                                               |

**Reciter.** `status: "identified"` gives `id`, `name_ar`, `name_en`, `style`,
`similarity` and up to two `alternatives`. `status: "unknown"` gives no name:
`id`, `name_ar`, `name_en` and `style` are null, `similarity` is the best
score seen, and `alternatives` holds up to two best guesses, for a
"may also be" line. An unknown reciter is a normal outcome, not an error.

**Ambiguous results and "listen longer".** Some passages repeat. When a result
is ambiguous, record another clip and send it with
`previous_identify_id=<id of the ambiguous result>`. If exactly one of the
earlier candidates is followed by the new clip's location, the answer comes
back as a `match` there. The server keeps only the candidates' positions, for
5 minutes; it keeps no audio and no transcript.

### Errors

| HTTP | `code`                                  | When                                                                                      |
| ---- | --------------------------------------- | ----------------------------------------------------------------------------------------- |
| 413  | `audio_too_large` / `payload_too_large` | Upload over `MAX_UPLOAD_MB`.                                                              |
| 422  | `audio_unreadable`                      | Not decodable as audio.                                                                   |
| 422  | `audio_too_long`                        | Longer than `MAX_CLIP_SEC` (15 s).                                                        |
| 422  | `invalid_request`                       | Missing `audio`, bad `client`, malformed id.                                              |
| 429  | `rate_limited`                          | Over `RATE_LIMIT_PER_MIN` for this IP or device. `Retry-After` gives the wait in seconds. |
| 503  | `not_ready`                             | Models still loading (see `/readyz`).                                                     |
| 503  | `server_busy`                           | All model slots busy for too long. `Retry-After: 2`.                                      |

A clip that is too short, silent or not recitation is **not** an error: it is
a 200 with `status: "no_match"`.

### Privacy

The clip is decoded and processed in memory and is gone when the response is
sent. It is never written to disk, stored in a database or logged, and neither
is its transcript. What is recorded per request: outcome, scores, clip length,
timings, `client` and app version.

## Quran metadata

| Method | Path                                 | Returns                                                                                                                                                                                              |
| ------ | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GET    | `/v1/surahs`                         | All 114 surahs: `number`, `name_ar`, `name_en`, `ayah_count`, `revelation`; plus `text_attribution`.                                                                                                 |
| GET    | `/v1/surahs/{number}`                | The same for one surah, plus `first_page`, `first_juz` and `basmala_uthmani` (null for surahs 1 and 9).                                                                                              |
| GET    | `/v1/ayahs/{surah}/{ayah}?context=N` | The ayah (same object as in identify), `basmala_uthmani` (set on ayah 1 of surahs that open with one), and `context.before` / `context.after`: up to `N` (0–5) neighbouring ayahs in the same surah. |

Ayah text is the Tanzil Uthmani text, unmodified. **Wherever it is shown, the
app must credit Tanzil Project and link to tanzil.net**; `text_attribution`
carries the wording.

## Reciters

| Method | Path                                | Returns                                                                                                                      |
| ------ | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| GET    | `/v1/reciters`                      | `id`, `name_ar`, `name_en`, `country`, `styles` for every active reciter, ordered by English name.                           |
| GET    | `/v1/reciters/{id}`                 | The same, plus `ayah_audio`: for each style, a `url_template` with `{sss}` and `{aaa}` (zero-padded 3-digit surah and ayah). |
| GET    | `/v1/reciters/{id}?surah=67&ayah=1` | As above, with a ready `url` for that ayah in each entry ("continue listening from this ayah").                              |

- `country` is currently null for every reciter (no source for it yet).
- There are no reciter photos and no field for one.
- Audio links point at EveryAyah's per-ayah files. Full-surah links are not
  returned yet.

## `POST /v1/feedback`

```json
{
  "identify_id": "92738cd4-030e-4975-a886-a856eeb642e6",
  "kind": "wrong_ayah",
  "correct_surah": 67,
  "correct_ayah": 2
}
```

`kind` is `wrong_ayah`, `wrong_reciter` or `other`. `correct_surah` and
`correct_ayah` go together; `correct_reciter_id` must be a known reciter. All
three are optional. Returns `201 {"stored": true}`; `503 feedback_unavailable`
when there is no database. Rate limited like identify.

## Ops

| Method | Path       | Purpose                                                                                                           |
| ------ | ---------- | ----------------------------------------------------------------------------------------------------------------- |
| GET    | `/healthz` | Liveness. `200 {"status": "ok"}` while the process serves.                                                        |
| GET    | `/readyz`  | Readiness. `200` once the index, models and gallery are loaded and the configured stores answer; otherwise `503`. |
| GET    | `/metrics` | Prometheus text format.                                                                                           |

`/readyz` body:

```json
{
  "status": "ready",
  "components": {
    "quran_index": "ready",
    "asr_model": "ready",
    "speaker_model": "ready",
    "reciter_gallery": "ready"
  },
  "dependencies": { "database": true, "redis": true }
}
```

Each component is `pending`, `ready` or `failed`. `dependencies` lists only
configured stores.

### Metrics

| Name                                    | Type      | Labels                                            |
| --------------------------------------- | --------- | ------------------------------------------------- |
| `ansit_identify_total`                  | counter   | `status`, `reason`, `client`                      |
| `ansit_identify_stage_duration_seconds` | histogram | `stage` (decode, vad, asr, match, speaker, total) |
| `ansit_text_confidence`                 | histogram | —                                                 |
| `ansit_reciter_similarity`              | histogram | `status`                                          |
| `ansit_reciter_total`                   | counter   | `status`                                          |
| `ansit_identify_rejected_total`         | counter   | `code`                                            |
| `ansit_identify_in_flight`              | gauge     | —                                                 |
| `ansit_rate_limited_total`              | counter   | `scope` (ip, device)                              |
| `ansit_http_requests_total`             | counter   | `method`, `route` (template), `status`            |
| `ansit_http_request_duration_seconds`   | histogram | `method`, `route`                                 |
| `ansit_ready`                           | gauge     | —                                                 |

The confidence and similarity histograms are there for tuning
`MATCH_THRESHOLD` and `RECITER_THRESHOLD` on real traffic.
