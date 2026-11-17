"""The reciter gallery and open-set scoring.

A *voice* is one reciter in one recitation style (murattal, mujawwad, muallim).
Each voice has a set of clip embeddings and a centroid. A reciter's score for a
query is the best score among their voices, so a reciter is recognised in any
style the gallery holds, and styles do not blur each other's centroids.

Score of a voice = weight * cos(query, centroid)
                 + (1 - weight) * mean of the top-k cos(query, clip).

All embeddings are L2-normalized, so cosine similarity is a dot product. The
gallery is a few thousand 192-d vectors; scoring it exhaustively in NumPy takes
well under a millisecond.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import numpy.typing as npt

from app.speaker.engine import EMBEDDING_DIM, Embedding, l2_normalize

Style = Literal["murattal", "mujawwad", "muallim"]
TOP_K = 5
CENTROID_WEIGHT = 0.5
MAX_ALTERNATIVES = 2


@dataclass(frozen=True)
class Voice:
    reciter_id: str
    style: Style


@dataclass(frozen=True)
class ReciterScore:
    reciter_id: str
    style: Style
    """The style of this reciter's best-scoring voice."""
    similarity: float


@dataclass(frozen=True)
class ReciterResult:
    status: Literal["identified", "unknown"]
    best: ReciterScore | None
    """The top-scoring reciter, also when rejected (None for an empty gallery)."""
    alternatives: tuple[ReciterScore, ...]
    margin: float | None = None
    """Best score minus the runner-up's (None with fewer than two reciters)."""


class Gallery:
    def __init__(
        self,
        voices: list[Voice],
        embeddings: npt.NDArray[np.float32],
        voice_of_clip: npt.NDArray[np.intp],
        *,
        top_k: int = TOP_K,
        centroid_weight: float = CENTROID_WEIGHT,
    ) -> None:
        if embeddings.ndim != 2 or embeddings.shape[1] != EMBEDDING_DIM:
            raise ValueError(f"embeddings must be (n, {EMBEDDING_DIM}), got {embeddings.shape}")
        if len(voice_of_clip) != len(embeddings):
            raise ValueError("voice_of_clip and embeddings differ in length")
        if len(embeddings) and not np.allclose(np.linalg.norm(embeddings, axis=1), 1.0, atol=1e-3):
            raise ValueError("gallery embeddings must be L2-normalized")
        if len(set(voices)) != len(voices):
            raise ValueError("duplicate voices")
        counts = np.bincount(voice_of_clip, minlength=len(voices))
        if len(voice_of_clip) and (
            int(np.max(voice_of_clip)) >= len(voices) or (counts == 0).any()
        ):
            raise ValueError("every voice needs at least one clip")

        self.voices = voices
        self.embeddings = embeddings
        self.voice_of_clip = voice_of_clip
        self.top_k = top_k
        self.centroid_weight = centroid_weight
        self._clips_of_voice = [np.flatnonzero(voice_of_clip == v) for v in range(len(voices))]
        self.centroids = (
            np.stack([l2_normalize(embeddings[rows].mean(axis=0)) for rows in self._clips_of_voice])
            if voices
            else np.zeros((0, EMBEDDING_DIM), dtype=np.float32)
        )

    # ----------------------------------------------------------------- scoring

    def voice_scores(self, query: Embedding) -> npt.NDArray[np.float32]:
        """Score of every voice, in `self.voices` order."""
        clip_sims = self.embeddings @ query
        centroid_sims = self.centroids @ query
        scores = np.empty(len(self.voices), dtype=np.float32)
        for v, rows in enumerate(self._clips_of_voice):
            sims = clip_sims[rows]
            k = min(self.top_k, len(sims))
            top = np.partition(sims, len(sims) - k)[len(sims) - k :]
            scores[v] = (
                self.centroid_weight * centroid_sims[v] + (1.0 - self.centroid_weight) * top.mean()
            )
        return scores

    def rank(self, query: Embedding) -> list[ReciterScore]:
        """Reciters by descending score; each reciter appears once (best voice)."""
        scores = self.voice_scores(query)
        best: dict[str, ReciterScore] = {}
        for voice, score in zip(self.voices, scores, strict=True):
            current = best.get(voice.reciter_id)
            if current is None or score > current.similarity:
                best[voice.reciter_id] = ReciterScore(voice.reciter_id, voice.style, float(score))
        return sorted(best.values(), key=lambda s: (-s.similarity, s.reciter_id))

    def identify(
        self, query: Embedding, threshold: float, min_margin: float = 0.0
    ) -> ReciterResult:
        """Open-set decision.

        `identified` needs both: the best score at least `threshold`, and a lead
        of at least `min_margin` over the runner-up. The margin matters because
        absolute scores drop for everyone on degraded audio (phone, reverb),
        while a real match still stands clear of the next reciter.
        """
        ranked = self.rank(query)
        if not ranked:
            return ReciterResult("unknown", None, ())
        best = ranked[0]
        margin = best.similarity - ranked[1].similarity if len(ranked) > 1 else None
        accepted = best.similarity >= threshold and (margin is None or margin >= min_margin)
        return ReciterResult(
            "identified" if accepted else "unknown",
            best,
            tuple(ranked[1 : 1 + MAX_ALTERNATIVES]),
            margin,
        )

    # -------------------------------------------------------------- derivation

    def without_reciter(self, reciter_id: str) -> "Gallery":
        """A copy with one reciter removed (used for open-set evaluation)."""
        keep_voice = [v for v, voice in enumerate(self.voices) if voice.reciter_id != reciter_id]
        remap = {old: new for new, old in enumerate(keep_voice)}
        keep_clip = np.array([v in remap for v in self.voice_of_clip], dtype=bool)
        return Gallery(
            [self.voices[v] for v in keep_voice],
            self.embeddings[keep_clip],
            np.array([remap[v] for v in self.voice_of_clip[keep_clip]], dtype=np.intp),
            top_k=self.top_k,
            centroid_weight=self.centroid_weight,
        )

    # ------------------------------------------------------------- persistence

    def save(self, path: Path) -> None:
        """Embeddings only: no audio is stored anywhere in the gallery."""
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            embeddings=self.embeddings,
            voice_of_clip=self.voice_of_clip,
            voices=np.array(json.dumps([[v.reciter_id, v.style] for v in self.voices])),
        )

    @classmethod
    def load(cls, path: Path) -> "Gallery":
        if not path.is_file():
            raise FileNotFoundError(f"no gallery at {path} - run `make gallery`")
        with np.load(path, allow_pickle=False) as data:
            voices = [Voice(r, s) for r, s in json.loads(str(data["voices"]))]
            return cls(
                voices,
                data["embeddings"].astype(np.float32),
                data["voice_of_clip"].astype(np.intp),
            )
