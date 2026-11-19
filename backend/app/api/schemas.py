"""Request and response models for the public API. Field names are a contract:
add fields, never rename or remove them."""

import uuid
from typing import Literal

from pydantic import BaseModel, Field

Revelation = Literal["meccan", "medinan"]
Style = Literal["murattal", "mujawwad", "muallim"]
Client = Literal["web", "ios", "android"]

TEXT_ATTRIBUTION = "Tanzil Project — tanzil.net (Uthmani text, shown unmodified)"


# ------------------------------------------------------------------ identify


class AyahOut(BaseModel):
    surah: int
    surah_name_ar: str
    surah_name_en: str
    ayah: int
    text_uthmani: str = Field(description="Verbatim from Tanzil; never modified.")
    juz: int
    page: int
    revelation: Revelation
    ayah_count: int = Field(description="Number of ayahs in the surah.")


class WordRefOut(BaseModel):
    surah: int
    ayah: int
    word: int = Field(description="1-based word position inside the ayah.")


class SpanOut(BaseModel):
    start: WordRefOut
    end: WordRefOut


class CandidateOut(BaseModel):
    surah: int
    surah_name_ar: str
    ayah: int
    score: float = Field(description="0-1.")
    context_before: str | None = Field(
        description="Uthmani text of the preceding ayah, to help the user pick. "
        "Null for the first ayah of a surah."
    )


class ReciterAlternativeOut(BaseModel):
    id: str
    name_ar: str
    name_en: str
    style: Style
    similarity: float


class ReciterOut(BaseModel):
    status: Literal["identified", "unknown"]
    id: str | None = None
    name_ar: str | None = None
    name_en: str | None = None
    style: Style | None = None
    similarity: float | None = Field(
        default=None, description="Voice similarity of the best candidate, also when unknown."
    )
    alternatives: list[ReciterAlternativeOut] = Field(
        default_factory=list, description="Up to 2 other possibilities."
    )


class TimingsOut(BaseModel):
    decode: float = 0
    vad: float = 0
    asr: float = 0
    match: float = 0
    speaker: float = 0
    total: float = 0


class DebugOut(BaseModel):
    transcript_normalized: str | None
    prefix_detected: str | None


class IdentifyResponse(BaseModel):
    id: uuid.UUID
    status: Literal["match", "ambiguous", "no_match"]
    reason: Literal["no_speech", "too_short", "low_confidence"] | None = None
    ayah: AyahOut | None = None
    span: SpanOut | None = None
    text_confidence: float | None = Field(default=None, description="0-1.")
    candidates: list[CandidateOut] = Field(
        default_factory=list, description="When ambiguous: up to 5 possible locations."
    )
    repeated_count: int | None = Field(
        default=None, description="When ambiguous: how many locations there are in total."
    )
    reciter: ReciterOut | None = Field(
        default=None, description="Null when no recitation was identified."
    )
    timings_ms: TimingsOut
    debug: DebugOut | None = Field(
        default=None, description="Only with debug=true and ALLOW_DEBUG on the server."
    )


# --------------------------------------------------------------------- quran


class SurahOut(BaseModel):
    number: int
    name_ar: str
    name_en: str
    ayah_count: int
    revelation: Revelation


class SurahDetailOut(SurahOut):
    first_page: int
    first_juz: int
    basmala_uthmani: str | None = Field(
        description="The basmala recited before the surah (null for surah 1, where it "
        "is ayah 1, and surah 9, which has none)."
    )


class SurahListOut(BaseModel):
    surahs: list[SurahOut]
    text_attribution: str = TEXT_ATTRIBUTION


class AyahTextOut(BaseModel):
    surah: int
    ayah: int
    text_uthmani: str
    juz: int
    page: int


class AyahContextOut(BaseModel):
    before: list[AyahTextOut]
    after: list[AyahTextOut]


class AyahDetailOut(BaseModel):
    ayah: AyahOut
    basmala_uthmani: str | None
    context: AyahContextOut
    text_attribution: str = TEXT_ATTRIBUTION


class TafsirOut(BaseModel):
    surah: int
    ayah: int
    text: str = Field(description="Verbatim tafsir text from the named source.")
    source_key: str
    book: str
    author: str
    publisher: str
    version: str
    source_url: str
    attribution: str


# ------------------------------------------------------------------ reciters


class ReciterSummaryOut(BaseModel):
    id: str
    name_ar: str
    name_en: str
    country: str | None
    styles: list[Style]


class ReciterListOut(BaseModel):
    reciters: list[ReciterSummaryOut]


class AyahAudioOut(BaseModel):
    style: Style
    url_template: str = Field(
        description="Replace {sss} and {aaa} with the zero-padded 3-digit surah and ayah."
    )
    url: str | None = Field(
        default=None, description="Filled in when the request names a surah and ayah."
    )


class ReciterDetailOut(ReciterSummaryOut):
    ayah_audio: list[AyahAudioOut]


# ------------------------------------------------------------------ feedback


class FeedbackIn(BaseModel):
    identify_id: uuid.UUID
    kind: Literal["wrong_ayah", "wrong_reciter", "other"]
    correct_surah: int | None = Field(default=None, ge=1, le=114)
    correct_ayah: int | None = Field(default=None, ge=1)
    correct_reciter_id: str | None = Field(default=None, max_length=64)


class FeedbackOut(BaseModel):
    stored: bool


# -------------------------------------------------------------------- errors


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorOut(BaseModel):
    error: ErrorBody
