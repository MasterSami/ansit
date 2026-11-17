"""Decode an uploaded clip to 16 kHz mono float32, entirely in memory.

Decoding uses the FFmpeg libraries through PyAV on an in-memory buffer, so the
clip is never written to disk (privacy rule: audio is not persisted). A seekable
buffer also handles MP4/M4A files whose index sits at the end, as iOS writes them.
"""

import io
from typing import Any, Literal

import av
import numpy as np
import numpy.typing as npt

SAMPLE_RATE = 16_000
Waveform = npt.NDArray[np.float32]
AudioErrorReason = Literal["decode_failed", "too_large", "too_long", "no_audio"]


class AudioError(Exception):
    """The upload cannot be used. `reason` is safe to return to a client."""

    def __init__(self, reason: AudioErrorReason, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason


def decode_audio(data: bytes, *, max_bytes: int, max_seconds: float) -> Waveform:
    """Decode webm/opus, m4a/aac, mp3, wav... to 16 kHz mono float32 in [-1, 1].

    Raises AudioError if the upload is too large, not decodable, has no audio
    stream, or is longer than `max_seconds` (decoding stops as soon as it is).
    """
    if len(data) > max_bytes:
        raise AudioError("too_large", f"{len(data)} bytes > {max_bytes}")
    if not data:
        raise AudioError("decode_failed", "empty upload")

    max_samples = int(max_seconds * SAMPLE_RATE)
    chunks: list[npt.NDArray[Any]] = []
    total = 0
    try:
        with av.open(io.BytesIO(data), mode="r") as container:
            if not container.streams.audio:
                raise AudioError("no_audio")
            resampler = av.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
            for frame in container.decode(container.streams.audio[0]):
                for out in resampler.resample(frame):
                    chunk = out.to_ndarray().reshape(-1)
                    chunks.append(chunk)
                    total += len(chunk)
                if total > max_samples:
                    raise AudioError("too_long", f"longer than {max_seconds:g} s")
            for out in resampler.resample(None):  # flush
                chunk = out.to_ndarray().reshape(-1)
                chunks.append(chunk)
                total += len(chunk)
    except AudioError:
        raise
    except (av.error.FFmpegError, ValueError, IndexError, OSError) as exc:
        raise AudioError("decode_failed", type(exc).__name__) from exc

    if total > max_samples:
        raise AudioError("too_long", f"longer than {max_seconds:g} s")
    if total == 0:
        raise AudioError("no_audio")
    return np.concatenate(chunks).astype(np.float32) / 32768.0
