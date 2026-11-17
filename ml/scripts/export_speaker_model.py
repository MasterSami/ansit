"""Export the ECAPA-TDNN speaker model to ONNX and verify it against SpeechBrain.

Usage: uv run --project backend --group ml python ml/scripts/export_speaker_model.py

Output: ml/artifacts/speaker/ecapa.onnx (+ SOURCE.json). The service runs this
file with ONNX Runtime and computes the input features in NumPy
(`app/speaker/features.py`), so it needs no PyTorch.

The export is refused unless NumPy features + ONNX reproduce SpeechBrain's own
embeddings (cosine similarity above 0.9999) on several test signals.
"""

import json
import sys
import warnings
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.audio.decode import SAMPLE_RATE
from app.speaker.engine import EMBEDDING_DIM, OnnxEcapaEngine, l2_normalize

SOURCE_REPO = "speechbrain/spkrec-ecapa-voxceleb"
# Pinned commit; verified in docs/DATA_SOURCES.md (Apache-2.0).
SOURCE_COMMIT = "0f99f2d0ebe89ac095bcc5903c4dd8f72b367286"
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
        voiced = sum(
            np.sin(2 * np.pi * k * np.cumsum(pitch) / SAMPLE_RATE) / k for k in range(1, 9)
        )
        envelope = 0.5 * (1 + np.sin(2 * np.pi * 2.3 * t))
        signals.append((0.2 * voiced * envelope + 0.01 * rng.standard_normal(n)).astype(np.float32))
    return signals


def main() -> int:
    import torch
    from huggingface_hub import snapshot_download
    from speechbrain.inference.speaker import EncoderClassifier

    warnings.filterwarnings("ignore")
    # SpeechBrain cannot pin a revision itself, so fetch the pinned commit first
    # and load from that local copy.
    source_dir = snapshot_download(
        SOURCE_REPO, revision=SOURCE_COMMIT, local_dir=str(OUT_DIR / "source")
    )
    classifier = EncoderClassifier.from_hparams(
        source=source_dir, savedir=source_dir, run_opts={"device": "cpu"}
    )
    classifier.eval()

    class EmbeddingOnly(torch.nn.Module):
        def __init__(self, model: torch.nn.Module) -> None:
            super().__init__()
            self.model = model

        def forward(self, feats: torch.Tensor) -> torch.Tensor:
            return self.model(feats).squeeze(1)

    signals = test_signals()
    with torch.no_grad():
        example = classifier.mods.compute_features(torch.from_numpy(signals[0])[None])
        example = classifier.mods.mean_var_norm(example, torch.ones(1))
    onnx_path = OUT_DIR / "ecapa.onnx"
    torch.onnx.export(
        EmbeddingOnly(classifier.mods.embedding_model).eval(),
        (example,),
        str(onnx_path),
        input_names=["feats"],
        output_names=["embedding"],
        dynamic_axes={"feats": {0: "batch", 1: "time"}, "embedding": {0: "batch"}},
        opset_version=17,
        dynamo=False,
    )

    engine = OnnxEcapaEngine(onnx_path)
    worst = 1.0
    for signal in signals:
        with torch.no_grad():
            reference = classifier.encode_batch(torch.from_numpy(signal)[None]).squeeze().numpy()
        ours = engine.embed(signal)
        if ours.shape != (EMBEDDING_DIM,):
            raise SystemExit(f"unexpected embedding shape {ours.shape}")
        worst = min(worst, float(ours @ l2_normalize(reference)))
    print(f"parity    worst cosine vs SpeechBrain over {len(signals)} signals: {worst:.6f}")
    if worst < MIN_PARITY:
        onnx_path.unlink()
        raise SystemExit(f"parity {worst:.6f} < {MIN_PARITY}: export rejected")

    (OUT_DIR / "SOURCE.json").write_text(
        json.dumps(
            {
                "repo": SOURCE_REPO,
                "commit": SOURCE_COMMIT,
                "license": "apache-2.0",
                "format": "onnx opset 17",
                "embedding_dim": EMBEDDING_DIM,
                "parity_cosine": round(worst, 6),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"wrote     {onnx_path.relative_to(REPO)}  ({onnx_path.stat().st_size / 1e6:.0f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
