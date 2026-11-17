from pathlib import Path

import numpy as np
import pytest

from app.audio.decode import SAMPLE_RATE, Waveform
from app.speaker.engine import EMBEDDING_DIM, OnnxEcapaEngine
from app.speaker.features import HOP, N_MELS, fbank
from tests.audio.helpers import tone

REPO = Path(__file__).resolve().parents[3]
MODEL = REPO / "ml" / "artifacts" / "speaker" / "ecapa.onnx"


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
    assert features.shape == (1 + 2 * SAMPLE_RATE // HOP, N_MELS)


def test_fbank_is_mean_normalized_over_time() -> None:
    features = fbank(voiced(3.0, 140, seed=1))
    assert np.allclose(features.mean(axis=0), 0.0, atol=1e-3)


def test_fbank_is_volume_invariant() -> None:
    """Log-mel minus its mean removes overall gain (as long as nothing clips to the floor)."""
    signal = voiced(2.0, 120, seed=2)
    assert np.allclose(fbank(signal), fbank(signal * 0.25), atol=1e-2)


def test_fbank_tracks_frequency() -> None:
    low = fbank(tone(1.0, 300.0)).var(axis=0)  # which mel bin moves... use energy instead
    del low
    low_bin = int(np.argmax(_mel_energy(tone(1.0, 300.0))))
    high_bin = int(np.argmax(_mel_energy(tone(1.0, 3000.0))))
    assert low_bin < high_bin


def _mel_energy(signal: Waveform) -> np.ndarray:
    from app.speaker import features as f

    padded = np.pad(signal.astype(np.float64), f.N_FFT // 2)
    frame = padded[: f.N_FFT] * f._window()
    return np.asarray((np.abs(np.fft.rfft(frame)) ** 2) @ f._mel_filterbank().T)


def test_fbank_rejects_too_short_input() -> None:
    with pytest.raises(ValueError):
        fbank(np.zeros(100, dtype=np.float32))


def test_fbank_matches_speechbrain() -> None:
    """Parity with the reference implementation; needs the `ml` dependency group."""
    torch = pytest.importorskip("torch")
    features = pytest.importorskip("speechbrain.lobes.features")
    processing = pytest.importorskip("speechbrain.processing.features")

    signal = voiced(4.0, 150, seed=3)
    with torch.no_grad():
        reference = features.Fbank(n_mels=80)(torch.from_numpy(signal)[None])
        reference = processing.InputNormalization(norm_type="sentence", std_norm=False)(
            reference, torch.ones(1)
        )
    ours = fbank(signal)
    assert ours.shape == tuple(reference.shape[1:])
    assert float(np.abs(ours - reference[0].numpy()).max()) < 5e-3


# --- engine ---


def test_missing_model_file_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="export_speaker_model"):
        OnnxEcapaEngine(tmp_path / "nope.onnx")


@pytest.fixture(scope="module")
def engine() -> OnnxEcapaEngine:
    if not MODEL.is_file():
        pytest.skip("speaker model not built; run ml/scripts/export_speaker_model.py")
    return OnnxEcapaEngine(MODEL)


def test_embedding_is_192d_and_normalized(engine: OnnxEcapaEngine) -> None:
    embedding = engine.embed(voiced(5.0, 130, seed=4))
    assert embedding.shape == (EMBEDDING_DIM,)
    assert embedding.dtype == np.float32
    assert float(np.linalg.norm(embedding)) == pytest.approx(1.0, abs=1e-5)


def test_embedding_is_deterministic_and_length_tolerant(engine: OnnxEcapaEngine) -> None:
    signal = voiced(8.0, 130, seed=5)
    first = engine.embed(signal)
    assert np.allclose(first, engine.embed(signal), atol=1e-6)
    # the same "voice", different lengths: still far closer than a different pitch
    same = float(first @ engine.embed(signal[: 5 * SAMPLE_RATE]))
    other = float(first @ engine.embed(voiced(8.0, 240, seed=6)))
    assert same > other
    engine.warm_up()
