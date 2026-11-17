"""Kaldi-compatible log-mel filterbank features for the speaker model, in NumPy.

The WeSpeaker ResNet34 model was trained on Kaldi `fbank` features (80 mel
bins, 25 ms window, 10 ms shift) followed by per-utterance mean subtraction.
Computing them in NumPy lets the service run the model with ONNX Runtime and no
PyTorch. `ml/scripts/fetch_speaker_model.py` checks parity against
torchaudio's Kaldi implementation every time the model is fetched.
"""

from functools import lru_cache

import numpy as np
import numpy.typing as npt

from app.audio.decode import SAMPLE_RATE, Waveform

FRAME_LENGTH = 400  # 25 ms
FRAME_SHIFT = 160  # 10 ms
N_FFT = 512  # next power of two above the frame length
N_MELS = 80
LOW_FREQ = 20.0
PREEMPHASIS = 0.97
_EPSILON = float(np.finfo(np.float32).eps)

Features = npt.NDArray[np.float32]


def _mel(hz: npt.NDArray[np.float64] | float) -> npt.NDArray[np.float64]:
    return np.asarray(1127.0 * np.log(1.0 + np.asarray(hz, dtype=np.float64) / 700.0))


@lru_cache(maxsize=1)
def _mel_filterbank() -> npt.NDArray[np.float64]:
    """Kaldi triangular filters (triangles in the mel domain), shape (N_MELS, N_FFT // 2)."""
    nyquist = SAMPLE_RATE / 2
    mel_low, mel_high = float(_mel(LOW_FREQ)), float(_mel(nyquist))
    delta = (mel_high - mel_low) / (N_MELS + 1)
    left = mel_low + delta * np.arange(N_MELS)[:, None]
    centre, right = left + delta, left + 2 * delta
    mel = _mel(np.arange(N_FFT // 2) * SAMPLE_RATE / N_FFT)[None, :]
    up = (mel - left) / (centre - left)
    down = (right - mel) / (right - centre)
    return np.asarray(np.maximum(0.0, np.minimum(up, down)))


@lru_cache(maxsize=1)
def _window() -> npt.NDArray[np.float64]:
    """Kaldi's "povey" window: a Hann window raised to the power 0.85."""
    n = np.arange(FRAME_LENGTH)
    return np.asarray((0.5 - 0.5 * np.cos(2.0 * np.pi * n / (FRAME_LENGTH - 1))) ** 0.85)


def fbank(waveform: Waveform) -> Features:
    """16 kHz mono float32 in [-1, 1] -> (frames, 80) mean-normalized log-mel features."""
    if len(waveform) < FRAME_LENGTH:
        raise ValueError("waveform shorter than one analysis window")
    signal = waveform.astype(np.float64) * 32768.0  # Kaldi works on 16-bit sample values
    n_frames = 1 + (len(signal) - FRAME_LENGTH) // FRAME_SHIFT
    index = np.arange(FRAME_LENGTH)[None, :] + FRAME_SHIFT * np.arange(n_frames)[:, None]
    frames = signal[index]

    frames = frames - frames.mean(axis=1, keepdims=True)  # remove DC offset
    previous = np.concatenate([frames[:, :1], frames[:, :-1]], axis=1)
    frames = (frames - PREEMPHASIS * previous) * _window()

    power = np.abs(np.fft.rfft(frames, n=N_FFT, axis=1)) ** 2
    mel = power[:, : N_FFT // 2] @ _mel_filterbank().T
    log_mel = np.log(np.maximum(mel, _EPSILON))
    return np.asarray(log_mel - log_mel.mean(axis=0, keepdims=True), dtype=np.float32)
