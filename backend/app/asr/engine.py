"""ASR engine interface. Implementations must be swappable behind it."""

from dataclasses import dataclass
from typing import Protocol

from app.audio.decode import Waveform


@dataclass(frozen=True)
class ASRResult:
    text: str
    avg_logprob: float
    """Mean token log-probability (duration-weighted over segments). 0 is certain."""
    no_speech_prob: float
    """Highest no-speech probability over segments."""
    duration_ms: float
    """Time spent in inference."""
    compression_ratio: float = 0.0
    """Highest gzip compression ratio over segments; high values mean repetition loops."""


class ASREngine(Protocol):
    def transcribe(self, waveform_16k: Waveform) -> ASRResult:
        """Transcribe 16 kHz mono float32 audio."""
        ...
