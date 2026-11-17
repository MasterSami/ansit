"""Hallucination guards: decide whether an ASR result can be trusted at all.

Whisper tends to produce fluent text for silence, noise or music. These checks
run before matching; a flagged result is treated as "no recitation detected".
"""

from dataclasses import dataclass
from itertools import pairwise
from typing import Literal

from app.asr.engine import ASRResult
from app.matcher.normalize import normalize_ar

GuardFlag = Literal["empty", "no_speech", "low_logprob", "repetition", "known_hallucination"]

# Phrases Whisper is known to invent on Arabic non-speech audio (subtitle credits
# and sign-offs from its training data). None of them is Quran text.
_KNOWN_HALLUCINATIONS = tuple(
    normalize_ar(phrase)
    for phrase in (
        "ترجمة نانسي قنقر",
        "اشتركوا في القناة",
        "شكرا على المشاهدة",
        "شكرا للمشاهدة",
        "لا تنسوا الاشتراك",
    )
)


@dataclass(frozen=True)
class GuardConfig:
    max_no_speech_prob: float = 0.6
    min_avg_logprob: float = -1.0
    max_compression_ratio: float = 2.4
    max_word_run: int = 6
    """Longest run of one identical word accepted."""


def check_asr_result(result: ASRResult, config: GuardConfig) -> list[GuardFlag]:
    """Returns the reasons to distrust `result`; an empty list means it passes."""
    flags: list[GuardFlag] = []
    words = normalize_ar(result.text).split()
    if not words:
        return ["empty"]
    if result.no_speech_prob > config.max_no_speech_prob:
        flags.append("no_speech")
    if result.avg_logprob < config.min_avg_logprob:
        flags.append("low_logprob")

    longest = run = 1
    for prev, cur in pairwise(words):
        run = run + 1 if cur == prev else 1
        longest = max(longest, run)
    if longest > config.max_word_run or result.compression_ratio > config.max_compression_ratio:
        flags.append("repetition")

    joined = " ".join(words)
    if any(phrase in joined for phrase in _KNOWN_HALLUCINATIONS):
        flags.append("known_hallucination")
    return flags
