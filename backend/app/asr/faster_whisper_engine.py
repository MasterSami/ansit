"""faster-whisper (CTranslate2) implementation of ASREngine."""

import time
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

from app.asr.engine import ASRResult
from app.audio.decode import SAMPLE_RATE, Waveform


class FasterWhisperEngine:
    def __init__(
        self,
        model_path: str | Path,
        *,
        device: str = "cpu",
        compute_type: str = "int8",
        cpu_threads: int = 2,
        beam_size: int = 5,
    ) -> None:
        path = Path(model_path)
        if not (path / "model.bin").is_file():
            raise FileNotFoundError(
                f"no CTranslate2 model in {path} - run ml/scripts/convert_models.py"
            )
        self.beam_size = beam_size
        self._model = WhisperModel(
            str(path),
            device=device,
            compute_type=compute_type,
            cpu_threads=cpu_threads,
            local_files_only=True,
        )

    def transcribe(self, waveform_16k: Waveform) -> ASRResult:
        started = time.perf_counter()
        segments, _ = self._model.transcribe(
            waveform_16k,
            language="ar",
            task="transcribe",
            beam_size=self.beam_size,
            without_timestamps=True,
            condition_on_previous_text=False,
            # No temperature fallback: retries multiply latency and are where
            # Whisper invents text. The guards reject low-confidence output instead.
            temperature=0.0,
            vad_filter=False,
        )
        parts = list(segments)  # the generator does the actual decoding
        elapsed_ms = (time.perf_counter() - started) * 1000
        if not parts:
            return ASRResult("", float("-inf"), 1.0, elapsed_ms)

        weights = [max(seg.end - seg.start, 1e-3) for seg in parts]
        return ASRResult(
            text=" ".join(seg.text.strip() for seg in parts).strip(),
            avg_logprob=float(np.average([seg.avg_logprob for seg in parts], weights=weights)),
            no_speech_prob=float(max(seg.no_speech_prob for seg in parts)),
            duration_ms=elapsed_ms,
            compression_ratio=float(max(seg.compression_ratio for seg in parts)),
        )

    def warm_up(self) -> None:
        """One pass so the first real request does not pay for lazy initialisation."""
        self.transcribe(np.zeros(SAMPLE_RATE * 3, dtype=np.float32))
