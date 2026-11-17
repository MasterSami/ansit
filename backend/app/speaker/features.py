"""Log-mel filterbank features for the ECAPA-TDNN speaker model, in NumPy.

This reproduces SpeechBrain's `Fbank(n_mels=80)` followed by sentence-level mean
normalization, which is what `speechbrain/spkrec-ecapa-voxceleb` was trained
with. Doing it in NumPy lets the service run the model with ONNX Runtime and no
PyTorch. `ml/scripts/export_speaker_model.py` checks parity against SpeechBrain
(embedding cosine similarity must be > 0.9999) every time the model is exported.
"""

from functools import lru_cache

import numpy as np
import numpy.typing as npt

from app.audio.decode import SAMPLE_RATE, Waveform

N_FFT = 400  # 25 ms window
HOP = 160  # 10 ms hop
N_MELS = 80
TOP_DB = 80.0
AMIN = 1e-10

Features = npt.NDArray[np.float32]


def _hz_to_mel(hz: npt.NDArray[np.float64] | float) -> npt.NDArray[np.float64]:
    return np.asarray(2595.0 * np.log10(1.0 + np.asarray(hz, dtype=np.float64) / 700.0))


@lru_cache(maxsize=1)
def _mel_filterbank() -> npt.NDArray[np.float64]:
    """Triangular filters, shape (N_MELS, N_FFT // 2 + 1)."""
    nyquist = SAMPLE_RATE / 2
    mel_points = np.linspace(_hz_to_mel(0.0), _hz_to_mel(nyquist), N_MELS + 2)
    hz = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)
    band = (hz[1:] - hz[:-1])[:-1]
    centre = hz[1:-1]
    freqs = np.linspace(0.0, nyquist, N_FFT // 2 + 1)
    slope = (freqs[None, :] - centre[:, None]) / band[:, None]
    return np.asarray(np.maximum(0.0, np.minimum(slope + 1.0, -slope + 1.0)))


@lru_cache(maxsize=1)
def _window() -> npt.NDArray[np.float64]:
    return np.hamming(N_FFT + 1)[:-1]  # periodic Hamming, as torch.hamming_window


def fbank(waveform: Waveform) -> Features:
    """16 kHz mono float32 -> (frames, 80) mean-normalized log-mel features."""
    if len(waveform) < N_FFT:
        raise ValueError("waveform shorter than one analysis window")
    padded = np.pad(waveform.astype(np.float64), N_FFT // 2)
    n_frames = 1 + (len(padded) - N_FFT) // HOP
    index = np.arange(N_FFT)[None, :] + HOP * np.arange(n_frames)[:, None]
    power = np.abs(np.fft.rfft(padded[index] * _window(), axis=1)) ** 2

    mel = power @ _mel_filterbank().T
    db = 10.0 * np.log10(np.maximum(mel, AMIN))
    db = np.maximum(db, float(np.max(db)) - TOP_DB)
    return np.asarray(db - db.mean(axis=0, keepdims=True), dtype=np.float32)
