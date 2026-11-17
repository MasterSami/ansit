"""Speaker embedding engines. Swappable behind `SpeakerEngine`."""

from pathlib import Path
from typing import Protocol

import numpy as np
import numpy.typing as npt
import onnxruntime as ort

from app.audio.decode import SAMPLE_RATE, Waveform
from app.speaker.features import fbank

EMBEDDING_DIM = 256
Embedding = npt.NDArray[np.float32]


def l2_normalize(vector: npt.NDArray[np.floating]) -> Embedding:
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        raise ValueError("cannot normalize a zero vector")
    return np.asarray(vector / norm, dtype=np.float32)


class SpeakerEngine(Protocol):
    def embed(self, waveform_16k: Waveform) -> Embedding:
        """Return an L2-normalized voice embedding of 16 kHz mono float32 audio."""
        ...


class OnnxSpeakerEngine:
    """WeSpeaker ResNet34 (VoxCeleb, large-margin fine-tuned) on ONNX Runtime, CPU.

    256-dimensional, L2-normalized embeddings. The model file is fetched and
    verified by ml/scripts/fetch_speaker_model.py.
    """

    def __init__(self, model_path: str | Path, *, cpu_threads: int = 2) -> None:
        path = Path(model_path)
        if not path.is_file():
            raise FileNotFoundError(
                f"no speaker model at {path} - run ml/scripts/fetch_speaker_model.py"
            )
        options = ort.SessionOptions()
        options.intra_op_num_threads = cpu_threads
        options.inter_op_num_threads = 1
        self._session = ort.InferenceSession(
            str(path), sess_options=options, providers=["CPUExecutionProvider"]
        )
        self._input = self._session.get_inputs()[0].name

    def embed(self, waveform_16k: Waveform) -> Embedding:
        features = fbank(waveform_16k)[None, :, :]
        (output,) = self._session.run(None, {self._input: features})
        embedding = np.asarray(output).reshape(-1)
        if embedding.shape != (EMBEDDING_DIM,):
            raise RuntimeError(f"unexpected embedding shape {embedding.shape}")
        return l2_normalize(embedding)

    def warm_up(self) -> None:
        rng = np.random.default_rng(0)
        self.embed((rng.standard_normal(SAMPLE_RATE * 3) * 0.01).astype(np.float32))
