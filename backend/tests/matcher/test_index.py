from pathlib import Path

import pytest

from app.matcher.index import QuranIndex, WordRef
from app.matcher.normalize import NormalizationConfig
from app.matcher.quran_data import QuranData, QuranDataError


def test_global_word_sequence(index: QuranIndex) -> None:
    assert len(index.words) == sum(len(a.words) for a in index.ayahs)
    assert len(index.word_ayah) == len(index.words)
    assert index.ayah_start[0] == 0
    for ayah_idx, ayah in enumerate(index.ayahs):
        start = index.ayah_start[ayah_idx]
        assert tuple(index.words[start : start + len(ayah.words)]) == ayah.words


def test_word_ref_maps_positions_to_surah_ayah_word(index: QuranIndex) -> None:
    assert index.word_ref(0) == WordRef(1, 1, 1)
    mulk = index.ayah_index(67, 1)
    start = index.ayah_start[mulk]
    assert index.word_ref(start) == WordRef(67, 1, 1)
    last = start + len(index.ayahs[mulk].words) - 1
    assert index.word_ref(last) == WordRef(67, 1, len(index.ayahs[mulk].words))
    assert index.word_ref(last + 1) == WordRef(67, 2, 1)
    final = index.word_ref(len(index.words) - 1)
    assert (final.surah, final.ayah) == (114, 6)


def test_basmala_is_not_in_the_sequence_outside_fatiha(index: QuranIndex) -> None:
    size = len(index.basmala_words)
    assert tuple(index.words[:size]) == index.basmala_words
    baqara = index.ayah_start[index.ayah_index(2, 1)]
    assert tuple(index.words[baqara : baqara + size]) != index.basmala_words
    # 1:1, plus the one place it occurs inside an ayah (27:30).
    refs = {index.word_ref(p) for p in index.occurrences(0, size - 1)}
    assert {(r.surah, r.ayah) for r in refs} == {(1, 1), (27, 30)}


def test_postings_point_at_their_ngrams(index: QuranIndex) -> None:
    for gram, positions in list(index.trigrams.items())[:500]:
        for pos in positions:
            assert " ".join(index.words[pos : pos + 3]) == gram
    assert sum(len(p) for p in index.unigrams.values()) == len(index.words)
    assert sum(len(p) for p in index.bigrams.values()) == len(index.words) - 1
    assert sum(len(p) for p in index.trigrams.values()) == len(index.words) - 2


def test_rahman_refrain_duplicate_group(index: QuranIndex) -> None:
    """The brief's example: the refrain of Ar-Rahman appears 31 times."""
    group = index.duplicate_groups[index.ayah_index(55, 13)]
    assert len(group) == 31
    assert {index.ayahs[i].surah for i in group} == {55}
    texts = {index.ayahs[i].words for i in group}
    assert len(texts) == 1


def test_duplicate_groups_are_consistent(index: QuranIndex) -> None:
    for member, group in index.duplicate_groups.items():
        assert member in group and len(group) > 1
        assert len({index.ayahs[i].words for i in group}) == 1
    assert index.ayah_index(2, 255) not in index.duplicate_groups  # Ayat al-Kursi is unique


def test_occurrences(index: QuranIndex) -> None:
    refrain = index.ayah_index(55, 13)
    start = index.ayah_start[refrain]
    end = start + len(index.ayahs[refrain].words) - 1
    assert len(index.occurrences(start, end)) == 31
    kursi = index.ayah_index(2, 255)
    start = index.ayah_start[kursi]
    assert index.occurrences(start, start + 9) == [start]
    # single- and two-word spans use the other posting lists
    assert start in index.occurrences(start, start)
    assert start in index.occurrences(start, start + 1)


def test_istiadha_is_derived_from_the_data(index: QuranIndex) -> None:
    assert len(index.istiadha_words) == 5
    assert index.istiadha_words[0] == index.ayahs[index.ayah_index(113, 1)].words[1]
    assert index.istiadha_words[1:] == index.ayahs[index.ayah_index(16, 98)].words[-4:]


def test_save_load_round_trip(index: QuranIndex, tmp_path: Path) -> None:
    path = tmp_path / "index.json.gz"
    index.save(path)
    loaded = QuranIndex.load(path)
    assert loaded.config == index.config
    assert loaded.words == index.words
    assert loaded.ayahs == index.ayahs
    assert loaded.surahs == index.surahs
    assert loaded.trigrams.keys() == index.trigrams.keys()
    assert loaded.duplicate_groups == index.duplicate_groups
    assert "Tanzil" in loaded.attribution

    again = tmp_path / "again.json.gz"
    index.save(again)
    assert again.read_bytes() == path.read_bytes()  # deterministic artifact


def test_load_rejects_missing_and_incomplete_artifacts(
    quran: QuranData, index: QuranIndex, tmp_path: Path
) -> None:
    with pytest.raises(QuranDataError, match="missing"):
        QuranIndex.load(tmp_path / "nope.json.gz")
    with pytest.raises(QuranDataError, match="6236"):
        QuranIndex(index.config, index.surahs, index.ayahs[:-1], index.attribution)


def test_config_is_stored_with_the_index(quran: QuranData, tmp_path: Path) -> None:
    built = QuranIndex.build(quran, NormalizationConfig("drop"))
    built.save(tmp_path / "drop.json.gz")
    assert QuranIndex.load(tmp_path / "drop.json.gz").config.standalone_hamza == "drop"
