"""Gallery scoring with synthetic embeddings (no model needed)."""

from pathlib import Path

import numpy as np
import pytest

from app.speaker.engine import EMBEDDING_DIM, Embedding, l2_normalize
from app.speaker.gallery import Gallery, Voice


def unit(seed: int) -> Embedding:
    return l2_normalize(np.random.default_rng(seed).standard_normal(EMBEDDING_DIM))


def near(centre: Embedding, seed: int, noise: float = 0.25) -> Embedding:
    jitter = np.random.default_rng(seed).standard_normal(EMBEDDING_DIM) / np.sqrt(EMBEDDING_DIM)
    return l2_normalize(centre + noise * jitter)


def build(spec: dict[Voice, Embedding], clips: int = 8) -> Gallery:
    voices = list(spec)
    vectors, owners = [], []
    for index, voice in enumerate(voices):
        for clip in range(clips):
            vectors.append(near(spec[voice], seed=1000 * index + clip))
            owners.append(index)
    return Gallery(voices, np.stack(vectors), np.asarray(owners, dtype=np.intp))


A, B, C = Voice("a", "murattal"), Voice("b", "murattal"), Voice("c", "murattal")
CENTRES = {A: unit(1), B: unit(2), C: unit(3)}


@pytest.fixture
def gallery() -> Gallery:
    return build(CENTRES)


def test_ranks_the_right_reciter_first(gallery: Gallery) -> None:
    ranked = gallery.rank(near(CENTRES[B], seed=99))
    assert [r.reciter_id for r in ranked] == ["b", *sorted(["a", "c"], key=lambda r: r)] or (
        ranked[0].reciter_id == "b"
    )
    assert ranked[0].similarity > 0.8
    assert ranked[1].similarity < 0.3
    assert {r.reciter_id for r in ranked} == {"a", "b", "c"}


def test_identified_above_threshold_with_at_most_two_alternatives(gallery: Gallery) -> None:
    result = gallery.identify(near(CENTRES[A], seed=5), threshold=0.6)
    assert result.status == "identified"
    assert result.best is not None and result.best.reciter_id == "a"
    assert len(result.alternatives) == 2
    assert all(alt.reciter_id != "a" for alt in result.alternatives)
    assert result.alternatives[0].similarity >= result.alternatives[1].similarity


def test_unknown_voice_is_rejected_but_best_guess_is_kept(gallery: Gallery) -> None:
    result = gallery.identify(unit(777), threshold=0.6)
    assert result.status == "unknown"
    assert result.best is not None  # available for "may also be", never shown as a match
    assert result.best.similarity < 0.6


def test_threshold_is_inclusive(gallery: Gallery) -> None:
    query = near(CENTRES[A], seed=5)
    score = gallery.rank(query)[0].similarity
    assert gallery.identify(query, threshold=score).status == "identified"
    assert gallery.identify(query, threshold=score + 1e-4).status == "unknown"


def test_margin_over_the_runner_up_is_required() -> None:
    """Two near-identical voices: the score is high but the lead is tiny."""
    twin = near(unit(1), seed=42, noise=0.05)
    gallery = build({A: unit(1), B: twin, C: unit(3)})
    query = near(unit(1), seed=7)
    confident = gallery.identify(query, threshold=0.5)
    assert confident.status == "identified"
    assert confident.margin is not None and 0 <= confident.margin < 0.1
    assert gallery.identify(query, threshold=0.5, min_margin=0.1).status == "unknown"
    # a voice with no near twin clears the same margin easily
    clear = gallery.identify(near(unit(3), seed=8), threshold=0.5, min_margin=0.1)
    assert clear.status == "identified"
    assert clear.margin is not None and clear.margin > 0.5


def test_single_reciter_gallery_has_no_margin() -> None:
    gallery = build({A: unit(1)})
    result = gallery.identify(near(unit(1), seed=2), threshold=0.5, min_margin=0.3)
    assert (result.status, result.margin, result.alternatives) == ("identified", None, ())


def test_score_combines_centroid_and_nearest_clips(gallery: Gallery) -> None:
    query = near(CENTRES[C], seed=11)
    index = gallery.voices.index(C)
    rows = np.flatnonzero(gallery.voice_of_clip == index)
    sims = np.sort(gallery.embeddings[rows] @ query)[-5:]
    expected = 0.5 * float(gallery.centroids[index] @ query) + 0.5 * float(sims.mean())
    assert gallery.voice_scores(query)[index] == pytest.approx(expected, abs=1e-5)


def test_centroids_are_normalized(gallery: Gallery) -> None:
    assert np.allclose(np.linalg.norm(gallery.centroids, axis=1), 1.0, atol=1e-5)


def test_a_reciter_is_scored_by_their_best_style() -> None:
    """Separate centroids per style: a mujawwad query finds the mujawwad voice."""
    murattal, mujawwad = Voice("a", "murattal"), Voice("a", "mujawwad")
    gallery = build({murattal: unit(1), mujawwad: unit(50), B: unit(2)})
    ranked = gallery.rank(near(unit(50), seed=3))
    assert [r.reciter_id for r in ranked] == ["a", "b"]  # one entry per reciter
    assert ranked[0].style == "mujawwad"
    assert gallery.rank(near(unit(1), seed=4))[0].style == "murattal"


def test_fewer_clips_than_top_k() -> None:
    gallery = build({A: unit(1), B: unit(2)}, clips=2)
    assert gallery.rank(near(unit(1), seed=9))[0].reciter_id == "a"


def test_without_reciter(gallery: Gallery) -> None:
    smaller = gallery.without_reciter("b")
    assert {v.reciter_id for v in smaller.voices} == {"a", "c"}
    assert len(smaller.embeddings) == 16
    query = near(CENTRES[B], seed=99)
    assert smaller.identify(query, threshold=0.6).status == "unknown"
    # the others score exactly as before
    full = {r.reciter_id: r.similarity for r in gallery.rank(query)}
    for score in smaller.rank(query):
        assert score.similarity == pytest.approx(full[score.reciter_id], abs=1e-6)


def test_empty_gallery_returns_unknown() -> None:
    empty = Gallery([], np.zeros((0, EMBEDDING_DIM), dtype=np.float32), np.zeros(0, dtype=np.intp))
    result = empty.identify(unit(1), threshold=0.5)
    assert (result.status, result.best, result.alternatives) == ("unknown", None, ())


def test_save_and_load(gallery: Gallery, tmp_path: Path) -> None:
    path = tmp_path / "gallery.npz"
    gallery.save(path)
    loaded = Gallery.load(path)
    assert loaded.voices == gallery.voices
    assert np.array_equal(loaded.embeddings, gallery.embeddings)
    assert np.array_equal(loaded.voice_of_clip, gallery.voice_of_clip)
    query = near(CENTRES[A], seed=1)
    assert loaded.rank(query) == gallery.rank(query)
    with pytest.raises(FileNotFoundError):
        Gallery.load(tmp_path / "missing.npz")


def test_rejects_malformed_input() -> None:
    good = np.stack([unit(1), unit(2)])
    owners = np.array([0, 1], dtype=np.intp)
    with pytest.raises(ValueError, match="L2-normalized"):
        Gallery([A, B], good * 3, owners)
    with pytest.raises(ValueError, match=r"\(n, 192\)"):
        Gallery([A, B], good[:, :100], owners)
    with pytest.raises(ValueError, match="differ in length"):
        Gallery([A, B], good, owners[:1])
    with pytest.raises(ValueError, match="at least one clip"):
        Gallery([A, B, C], good, owners)
    with pytest.raises(ValueError, match="duplicate"):
        Gallery([A, A], good, owners)


def test_l2_normalize_rejects_zero() -> None:
    with pytest.raises(ValueError):
        l2_normalize(np.zeros(EMBEDDING_DIM))
