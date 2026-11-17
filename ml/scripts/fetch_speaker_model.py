"""Download the speaker embedding model and verify it.

Usage: uv run --project backend --group ml python ml/scripts/fetch_speaker_model.py

Model: WeSpeaker ResNet34 (large-margin fine-tuned) trained on VoxCeleb2,
published as ONNX. License CC BY 4.0: credit the WeSpeaker project.

Output: ml/artifacts/speaker/resnet34.onnx (+ SOURCE.json). The service runs it
with ONNX Runtime and computes the input features in NumPy
(`app/speaker/features.py`), so it needs no PyTorch.

Two checks, both must pass:
- the file's SHA-256 matches the pinned value;
- NumPy features give the same embeddings as the reference Kaldi features in
  torchaudio (cosine similarity above 0.9999).
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.core.system_certs import use_system_certs_if_requested

use_system_certs_if_requested()

from app.audio.decode import SAMPLE_RATE
from app.speaker.engine import EMBEDDING_DIM, OnnxSpeakerEngine, l2_normalize

SOURCE_REPO = "Wespeaker/wespeaker-voxceleb-resnet34-LM"
SOURCE_FILE = "voxceleb_resnet34_LM.onnx"
# Pinned; verified in docs/DATA_SOURCES.md.
SOURCE_COMMIT = "f0c48c298fd835726c27956a5d617bad7115627e"
SHA256 = "7bb2f06e9df17cdf1ef14ee8a15ab08ed28e8d0ef5054ee135741560df2ec068"
OUT_DIR = REPO / "ml" / "artifacts" / "speaker"
MIN_PARITY = 0.9999


def test_signals() -> list[np.ndarray]:
    """Deterministic speech-like signals of different lengths (no recordings needed)."""
    rng = np.random.default_rng(7)
    signals = []
    for seconds in (3.0, 5.5, 8.0, 12.0):
        n = int(seconds * SAMPLE_RATE)
        t = np.arange(n) / SAMPLE_RATE
        pitch = 110 + 40 * np.sin(2 * np.pi * 0.4 * t + rng.uniform(0, 6))
        phase = np.cumsum(pitch) / SAMPLE_RATE
        voiced = sum(np.sin(2 * np.pi * k * phase) / k for k in range(1, 9))
        envelope = 0.5 * (1 + np.sin(2 * np.pi * 2.3 * t))
        signals.append((0.2 * voiced * envelope + 0.01 * rng.standard_normal(n)).astype(np.float32))
    return signals


def main() -> int:
    import onnxruntime as ort
    import torch
    import torchaudio
    from huggingface_hub import hf_hub_download

    cached = hf_hub_download(SOURCE_REPO, SOURCE_FILE, revision=SOURCE_COMMIT)
    digest = hashlib.sha256(Path(cached).read_bytes()).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"checksum mismatch: {digest} != {SHA256}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    model_path = OUT_DIR / "resnet34.onnx"
    shutil.copyfile(cached, model_path)

    engine = OnnxSpeakerEngine(model_path)
    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    worst = 1.0
    for signal in test_signals():
        reference_feats = torchaudio.compliance.kaldi.fbank(
            torch.from_numpy(signal)[None] * 32768,
            num_mel_bins=80,
            frame_length=25,
            frame_shift=10,
            dither=0.0,
            energy_floor=0.0,
            sample_frequency=SAMPLE_RATE,
        )
        reference_feats = (reference_feats - reference_feats.mean(0, keepdim=True)).numpy()
        (reference,) = session.run(None, {input_name: reference_feats[None]})
        ours = engine.embed(signal)
        if ours.shape != (EMBEDDING_DIM,):
            raise SystemExit(f"unexpected embedding shape {ours.shape}")
        worst = min(worst, float(ours @ l2_normalize(np.asarray(reference).reshape(-1))))
    print(f"parity    worst cosine vs torchaudio Kaldi features: {worst:.6f}")
    if worst < MIN_PARITY:
        model_path.unlink()
        raise SystemExit(f"parity {worst:.6f} < {MIN_PARITY}: model rejected")

    (OUT_DIR / "SOURCE.json").write_text(
        json.dumps(
            {
                "repo": SOURCE_REPO,
                "file": SOURCE_FILE,
                "commit": SOURCE_COMMIT,
                "sha256": SHA256,
                "license": "cc-by-4.0",
                "attribution": "WeSpeaker project (https://github.com/wenet-e2e/wespeaker)",
                "embedding_dim": EMBEDDING_DIM,
                "parity_cosine": round(worst, 6),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"wrote     {model_path.relative_to(REPO)}  ({model_path.stat().st_size / 1e6:.0f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
