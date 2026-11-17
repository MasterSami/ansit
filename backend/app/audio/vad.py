"""Voice activity detection with Silero VAD (the ONNX model bundled with faster-whisper).

Used as a gate: clips with too little speech are rejected before ASR runs.

Silero is trained on conversational speech and under-detects Quran recitation,
whose long sustained notes it often scores as non-speech, more so with reverb
and noise. Measured on the Phase 2 eval set, the usual threshold of 0.5 rejected
6.7% of clean and 32.6% of phone-like recitation clips outright. The default here
is therefore much lower (0.15), which still rejected every non-speech test clip
at the gate or in the later ASR guards. See ml/eval/reports/phase2.md.
"""

from dataclasses import dataclass

from faster_whisper.vad import VadOptions, get_speech_timestamps

from app.audio.decode import SAMPLE_RATE, Waveform


@dataclass(frozen=True)
class SpeechActivity:
    speech_sec: float
    """Total detected speech."""
    start: int
    end: int
    """Sample range from the first speech onset to the last offset (0, 0 if none)."""


class SpeechDetector:
    def __init__(self, threshold: float = 0.15, pad_ms: int = 200) -> None:
        self._options = VadOptions(
            threshold=threshold,
            min_speech_duration_ms=100,
            min_silence_duration_ms=300,
            speech_pad_ms=pad_ms,
        )

    def detect(self, waveform: Waveform) -> SpeechActivity:
        segments = get_speech_timestamps(waveform, self._options, sampling_rate=SAMPLE_RATE)
        if not segments:
            return SpeechActivity(0.0, 0, 0)
        samples = sum(seg["end"] - seg["start"] for seg in segments)
        start = max(0, int(segments[0]["start"]))
        end = min(len(waveform), int(segments[-1]["end"]))
        return SpeechActivity(samples / SAMPLE_RATE, start, end)

    def warm_up(self) -> None:
        import numpy as np

        self.detect(np.zeros(SAMPLE_RATE, dtype=np.float32))
