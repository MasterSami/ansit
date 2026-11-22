"""Ayah identification pipeline: bytes -> decode -> VAD -> ASR -> guards -> match.

Privacy: the clip lives only in memory for the duration of the call. Nothing
here logs audio or transcripts; the transcript is returned to the caller, which
decides whether a debug response may include it.
"""

import time
from dataclasses import dataclass, field
from typing import Literal

from app.asr.engine import ASREngine, ASRResult
from app.asr.guards import GuardConfig, GuardFlag, check_asr_result
from app.audio.decode import SAMPLE_RATE, Waveform, decode_audio
from app.audio.vad import SpeechDetector
from app.matcher.search import AyahMatcher, MatchResult

Status = Literal["match", "ambiguous", "no_match"]
Reason = Literal["no_speech", "too_short", "low_confidence"]


@dataclass(frozen=True)
class AudioLimits:
    max_upload_bytes: int = 2 * 1024 * 1024
    min_clip_sec: float = 3.0
    max_clip_sec: float = 15.0
    min_speech_sec: float = 1.5
    min_fallback_speech_sec: float = 0.75
    trim_silence: bool = False
    """Cut leading/trailing non-speech before ASR. Off by default: on recitation
    the detector's idea of where speech starts and ends is unreliable, and
    trimming lowered accuracy on phone-like audio (Phase 2 report)."""


@dataclass
class AyahIdentification:
    status: Status
    reason: Reason | None
    match: MatchResult | None = None
    asr: ASRResult | None = None
    guard_flags: list[GuardFlag] = field(default_factory=list)
    clip_sec: float = 0.0
    speech_sec: float = 0.0
    timings_ms: dict[str, float] = field(default_factory=dict)


class AyahIdentifier:
    def __init__(
        self,
        asr: ASREngine,
        matcher: AyahMatcher,
        vad: SpeechDetector,
        limits: AudioLimits | None = None,
        guards: GuardConfig | None = None,
        fallback_vad: SpeechDetector | None = None,
    ) -> None:
        self.asr = asr
        self.matcher = matcher
        self.vad = vad
        self.limits = limits or AudioLimits()
        self.guards = guards or GuardConfig()
        self.fallback_vad = fallback_vad

    def identify(self, data: bytes) -> AyahIdentification:
        """Raises AudioError for uploads that cannot be processed at all
        (undecodable, too large, too long). Everything else is a result."""
        started = time.perf_counter()
        prepared = self.prepare(data)
        result = prepared.rejected or self.transcribe_and_match(prepared)
        result.timings_ms["total"] = (time.perf_counter() - started) * 1000
        return result

    def prepare(self, data: bytes) -> "PreparedClip":
        """Decode and gate. `rejected` is set when no model needs to run."""
        timings: dict[str, float] = {}
        started = time.perf_counter()
        waveform = decode_audio(
            data,
            max_bytes=self.limits.max_upload_bytes,
            max_seconds=self.limits.max_clip_sec,
        )
        timings["decode"] = (time.perf_counter() - started) * 1000
        clip_sec = len(waveform) / SAMPLE_RATE
        if clip_sec < self.limits.min_clip_sec:
            rejected = AyahIdentification(
                "no_match", "too_short", clip_sec=clip_sec, timings_ms=timings
            )
            return PreparedClip(waveform, clip_sec, 0.0, timings, rejected)

        started = time.perf_counter()
        activity = self.vad.detect(waveform)
        speech_detected = activity.speech_sec >= self.limits.min_speech_sec
        # Only the borderline range can rescue recitation; a larger low-threshold
        # total is more consistent with continuous noise, so keep the normal gate.
        if not speech_detected and self.fallback_vad is not None:
            fallback_activity = self.fallback_vad.detect(waveform)
            if (
                self.limits.min_fallback_speech_sec
                <= fallback_activity.speech_sec
                < self.limits.min_speech_sec
            ):
                activity = fallback_activity
                speech_detected = True
        timings["vad"] = (time.perf_counter() - started) * 1000
        if not speech_detected:
            rejected = AyahIdentification(
                "no_match",
                "no_speech",
                clip_sec=clip_sec,
                speech_sec=activity.speech_sec,
                timings_ms=timings,
            )
            return PreparedClip(waveform, clip_sec, activity.speech_sec, timings, rejected)

        speech = waveform[activity.start : activity.end] if self.limits.trim_silence else waveform
        return PreparedClip(waveform, clip_sec, activity.speech_sec, timings, None, speech)

    def transcribe_and_match(self, clip: "PreparedClip") -> AyahIdentification:
        """ASR, hallucination guards and ayah matching on a prepared clip."""
        timings = dict(clip.timings_ms)
        started = time.perf_counter()
        asr = self.asr.transcribe(clip.speech if clip.speech is not None else clip.waveform)
        timings["asr"] = (time.perf_counter() - started) * 1000
        flags = check_asr_result(asr, self.guards)
        if flags:
            return AyahIdentification(
                "no_match",
                "no_speech" if "empty" in flags or "no_speech" in flags else "low_confidence",
                asr=asr,
                guard_flags=flags,
                clip_sec=clip.clip_sec,
                speech_sec=clip.speech_sec,
                timings_ms=timings,
            )

        started = time.perf_counter()
        match = self.matcher.search(asr.text)
        timings["match"] = (time.perf_counter() - started) * 1000
        return AyahIdentification(
            match.status,
            match.reason,
            match=match,
            asr=asr,
            clip_sec=clip.clip_sec,
            speech_sec=clip.speech_sec,
            timings_ms=timings,
        )


@dataclass
class PreparedClip:
    """A decoded clip that passed (or failed) the cheap checks before any model runs."""

    waveform: Waveform
    clip_sec: float
    speech_sec: float
    timings_ms: dict[str, float]
    rejected: AyahIdentification | None = None
    speech: Waveform | None = None
    """What ASR should hear: the whole clip, or the trimmed region if trimming is on."""
