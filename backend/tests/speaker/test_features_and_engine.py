from pathlib import Path

import numpy as np
import pytest

from app.audio.decode import SAMPLE_RATE, Waveform
from app.speaker.engine import EMBEDDING_DIM, OnnxSpeakerEngine
from app.speaker.features import FRAME_LENGTH, FRAME_SHIFT, N_MELS, fbank
from tests.audio.helpers import tone

REPO = Path(__file__).resolve().parents[3]
MODEL = REPO / "ml" / "artifacts" / "speaker" / "resnet34.onnx"


def voiced(seconds: float, pitch: float, seed: int) -> Waveform:
    """A harmonic, speech-like signal."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE
    signal = sum(np.sin(2 * np.pi * pitch * k * t) / k for k in range(1, 10))
    envelope = 0.5 * (1 + np.sin(2 * np.pi * 3 * t))
    return (0.2 * signal * envelope + 0.01 * rng.standard_normal(len(t))).astype(np.float32)


# --- features ---


def test_fbank_shape_and_dtype() -> None:
    features = fbank(tone(2.0))
    assert features.dtype == np.float32
    assert features.shape == (1 + (2 * SAMPLE_RATE - FRAME_LENGTH) // FRAME_SHIFT, N_MELS)


def test_fbank_is_mean_normalized_over_time() -> None:
    features = fbank(voiced(3.0, 140, seed=1))
    assert np.allclose(features.mean(axis=0), 0.0, atol=1e-3)


def test_fbank_is_volume_invariant() -> None:
    """Log-mel minus its mean removes overall gain."""
    signal = voiced(2.0, 120, seed=2)
    assert np.allclose(fbank(signal), fbank(signal * 0.25), atol=1e-2)


def test_mel_filters_cover_the_band_in_order() -> None:
    from app.speaker import features as f

    filters = f._mel_filterbank()
    assert filters.shape == (N_MELS, f.N_FFT // 2)
    assert (filters >= 0).all() and float(np.max(filters)) <= 1.0
    peaks = filters.argmax(axis=1)
    assert (np.diff(peaks) >= 0).all()  # centre frequencies increase
    assert peaks[0] <= 3 and peaks[-1] >= f.N_FFT // 2 - 12


def test_fbank_rejects_too_short_input() -> None:
    with pytest.raises(ValueError):
        fbank(np.zeros(100, dtype=np.float32))


def test_fbank_matches_kaldi_reference() -> None:
    """Parity with torchaudio's Kaldi implementation; needs the `ml` dependency group."""
    torch = pytest.importorskip("torch")
    torchaudio = pytest.importorskip("torchaudio")

    signal = voiced(4.0, 150, seed=3)
    reference = torchaudio.compliance.kaldi.fbank(
        torch.from_numpy(signal)[None] * 32768,
        num_mel_bins=80,
        frame_length=25,
        frame_shift=10,
        dither=0.0,
        energy_floor=0.0,
        sample_frequency=SAMPLE_RATE,
    )
    reference = (reference - reference.mean(0, keepdim=True)).numpy()
    ours = fbank(signal)
    assert ours.shape == reference.shape
    assert float(np.abs(ours - reference).max()) < 5e-2
    assert float(np.abs(ours - reference).mean()) < 1e-3


# --- engine ---


def test_missing_model_file_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="fetch_speaker_model"):
        OnnxSpeakerEngine(tmp_path / "nope.onnx")


@pytest.fixture(scope="module")
def engine() -> OnnxSpeakerEngine:
    if not MODEL.is_file():
        pytest.skip("speaker model not built; run ml/scripts/fetch_speaker_model.py")
    return OnnxSpeakerEngine(MODEL)


def test_embedding_has_the_model_dimension_and_is_normalized(engine: OnnxSpeakerEngine) -> None:
    embedding = engine.embed(voiced(5.0, 130, seed=4))
    assert embedding.shape == (EMBEDDING_DIM,)
    assert embedding.dtype == np.float32
    assert float(np.linalg.norm(embedding)) == pytest.approx(1.0, abs=1e-5)


def test_embedding_is_deterministic_and_length_tolerant(engine: OnnxSpeakerEngine) -> None:
    signal = voiced(8.0, 130, seed=5)
    first = engine.embed(signal)
    assert np.allclose(first, engine.embed(signal), atol=1e-6)
    # the same "voice", different lengths: still far closer than a different pitch
    same = float(first @ engine.embed(signal[: 5 * SAMPLE_RATE]))
    other = float(first @ engine.embed(voiced(8.0, 240, seed=6)))
    assert same > other
    engine.warm_up()
