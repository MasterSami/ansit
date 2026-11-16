import random

from app.matcher.index import QuranIndex, WordRef
from app.matcher.quran_data import QuranData
from app.matcher.search import AyahMatcher, MatchResult


def ayah_words(index: QuranIndex, surah: int, ayah: int) -> list[str]:
    return list(index.ayahs[index.ayah_index(surah, ayah)].words)


def ref(index: QuranIndex, result: MatchResult) -> tuple[int, int]:
    assert result.best is not None
    primary = index.ayahs[result.best.ayah_idx]
    return primary.surah, primary.ayah


# --- exact matches ---


def test_whole_ayah(index: QuranIndex, matcher: AyahMatcher) -> None:
    words = ayah_words(index, 67, 1)
    result = matcher.search_words(words)
    assert result.status == "match"
    assert result.best is not None
    assert result.best.score == 100
    assert ref(index, result) == (67, 1)
    assert result.best.start == WordRef(67, 1, 1)
    assert result.best.end == WordRef(67, 1, len(words))
    assert result.prefix_detected is None
    assert result.repeated_count is None


def test_raw_uthmani_text_with_diacritics(
    quran: QuranData, index: QuranIndex, matcher: AyahMatcher
) -> None:
    result = matcher.search(quran.ayah(36, 1).text_uthmani + " " + quran.ayah(36, 2).text_uthmani)
    assert result.status == "match"
    assert ref(index, result) == (36, 2)


def test_span_inside_one_ayah(index: QuranIndex, matcher: AyahMatcher) -> None:
    words = ayah_words(index, 2, 255)[10:22]
    result = matcher.search_words(words)
    assert result.status == "match"
    assert result.best is not None
    assert result.best.start == WordRef(2, 255, 11)
    assert result.best.end == WordRef(2, 255, 22)


def test_span_crossing_ayahs(index: QuranIndex, matcher: AyahMatcher) -> None:
    words = (
        ayah_words(index, 18, 9)[-3:] + ayah_words(index, 18, 10) + ayah_words(index, 18, 11)[:2]
    )
    result = matcher.search_words(words)
    assert result.status == "match"
    assert ref(index, result) == (18, 10)
    assert result.best is not None
    assert (result.best.start.ayah, result.best.end.ayah) == (9, 11)


def test_span_crossing_surahs(index: QuranIndex, matcher: AyahMatcher) -> None:
    """Surah 9 has no basmala, so 8:75 runs straight into 9:1."""
    tail, head = ayah_words(index, 8, 75)[-6:], ayah_words(index, 9, 1)[:5]
    result = matcher.search_words(tail + head)
    assert result.status == "match"
    assert result.best is not None
    assert result.best.start.surah == 8 and result.best.end.surah == 9
    assert ref(index, result) == (8, 75)


# --- noise ---


def test_tolerates_deletion_merge_and_split(index: QuranIndex, matcher: AyahMatcher) -> None:
    words = ayah_words(index, 2, 255)[:18]
    noisy = [*words[:3], *words[4:7], words[7] + words[8], *words[9:12]]
    noisy += [words[12][:2], words[12][2:], *words[13:]]
    result = matcher.search_words(noisy)
    assert result.status == "match"
    assert ref(index, result) == (2, 255)


def test_span_edges_do_not_spill_onto_neighbouring_words(
    index: QuranIndex, matcher: AyahMatcher
) -> None:
    """Regression: a longer (split-word) query used to pull in an extra word at
    the edge, which could flip the primary ayah to a neighbour."""
    tail, head = ayah_words(index, 2, 2)[-3:], ayah_words(index, 2, 3)[:5]
    split_at = max(range(len(head)), key=lambda i: len(head[i]))
    word = head[split_at]
    noisy_head = [*head[:split_at], word[: len(word) // 2], word[len(word) // 2 :]]
    noisy_head += head[split_at + 1 :]
    result = matcher.search_words(tail + noisy_head)

    assert result.best is not None
    start = index.ayah_start[index.ayah_index(2, 3)] - 3
    assert (result.best.start_idx, result.best.end_idx) == (start, start + 7)
    assert ref(index, result) == (2, 3)


# --- ambiguity ---


def test_rahman_refrain_is_ambiguous(index: QuranIndex, matcher: AyahMatcher) -> None:
    result = matcher.search_words(ayah_words(index, 55, 13))
    assert result.status == "ambiguous"
    assert result.repeated_count == 31
    assert len(result.alternatives) == 31
    located = [index.ayahs[c.ayah_idx] for c in result.alternatives]
    assert {a.surah for a in located} == {55}
    assert [a.ayah for a in located] == sorted(a.ayah for a in located)  # mushaf order
    assert (55, 13) in {(a.surah, a.ayah) for a in located}


def test_refrain_with_context_is_not_ambiguous(index: QuranIndex, matcher: AyahMatcher) -> None:
    words = ayah_words(index, 55, 12) + ayah_words(index, 55, 13)
    result = matcher.search_words(words)
    assert result.status == "match"
    assert result.best is not None
    assert (result.best.start.ayah, result.best.end.ayah) == (12, 13)


def test_repeated_phrase_inside_longer_ayahs_is_ambiguous(
    index: QuranIndex, matcher: AyahMatcher
) -> None:
    """Ambiguity is about the matched words, not only whole-ayah duplicates."""
    position = next(
        p
        for p in range(len(index.words) - 4)
        if len(index.occurrences(p, p + 3)) == 3
        and index.word_ayah[p] == index.word_ayah[p + 3]
        and len(index.ayahs[index.word_ayah[p]].words) > 8
    )
    result = matcher.search_words(index.words[position : position + 4])
    assert result.status == "ambiguous"
    assert result.repeated_count == 3
    assert index.word_ayah[position] in {c.ayah_idx for c in result.alternatives}


# --- isti'adha / basmala ---


def test_basmala_before_a_surah_is_stripped(index: QuranIndex, matcher: AyahMatcher) -> None:
    words = [*index.basmala_words, *ayah_words(index, 67, 1)]
    result = matcher.search_words(words)
    assert result.status == "match"
    assert result.prefix_detected == "basmala"
    assert result.best is not None and result.best.start == WordRef(67, 1, 1)


def test_istiadha_and_basmala(index: QuranIndex, matcher: AyahMatcher) -> None:
    passage = ayah_words(index, 36, 1) + ayah_words(index, 36, 2) + ayah_words(index, 36, 3)
    result = matcher.search_words([*index.istiadha_words, *index.basmala_words, *passage])
    assert result.status == "match"
    assert result.prefix_detected == "isti'adha+basmala"
    assert result.best is not None and result.best.start == WordRef(36, 1, 1)

    result = matcher.search_words([*index.istiadha_words, *ayah_words(index, 9, 1)])
    assert result.status == "match"
    assert result.prefix_detected == "isti'adha"
    assert ref(index, result) == (9, 1)


def test_fatiha_keeps_its_basmala(index: QuranIndex, matcher: AyahMatcher) -> None:
    """In Al-Fatiha the basmala is ayah 1, so it must not be stripped away."""
    words = ayah_words(index, 1, 1) + ayah_words(index, 1, 2) + ayah_words(index, 1, 3)
    result = matcher.search_words(words)
    assert result.status == "match"
    assert result.prefix_detected is None
    assert result.best is not None
    assert result.best.start == WordRef(1, 1, 1)
    assert result.best.end.ayah == 3

    with_istiadha = matcher.search_words([*index.istiadha_words, *words])
    assert with_istiadha.prefix_detected == "isti'adha"
    assert with_istiadha.best is not None and with_istiadha.best.start == WordRef(1, 1, 1)


def test_basmala_alone_is_fatiha_1(index: QuranIndex, matcher: AyahMatcher) -> None:
    result = matcher.search_words(list(index.basmala_words))
    assert result.best is not None
    assert (1, 1) in {
        (index.ayahs[c.ayah_idx].surah, index.ayahs[c.ayah_idx].ayah)
        for c in (result.alternatives or (result.best,))
    }


def test_istiadha_alone_is_no_match(index: QuranIndex, matcher: AyahMatcher) -> None:
    """It resembles 16:98 but is not Quran text; it must not be reported as that ayah."""
    result = matcher.search_words(list(index.istiadha_words))
    assert result.status == "no_match"
    assert result.reason == "too_short"
    assert result.prefix_detected == "isti'adha"


def test_noisy_prefix_is_still_detected(index: QuranIndex, matcher: AyahMatcher) -> None:
    basmala = list(index.basmala_words)
    merged = [basmala[0] + basmala[1], *basmala[2:]]  # ASR merged two words
    result = matcher.search_words([*merged, *ayah_words(index, 67, 1)])
    assert result.status == "match"
    assert result.prefix_detected == "basmala"
    assert ref(index, result) == (67, 1)


def test_basmala_between_two_surahs(index: QuranIndex, matcher: AyahMatcher) -> None:
    """Regression: reciting the end of one surah, a basmala, then the next surah."""
    tail = ayah_words(index, 113, 4) + ayah_words(index, 113, 5)
    head = ayah_words(index, 114, 1) + ayah_words(index, 114, 2)
    result = matcher.search_words([*tail, *index.basmala_words, *head])
    assert result.status == "match"
    assert result.best is not None
    assert result.best.score == 100
    assert result.best.start == WordRef(113, 4, 1)
    assert result.best.end.surah == 114


# --- no match ---


def test_too_short(matcher: AyahMatcher, index: QuranIndex) -> None:
    assert matcher.search_words([]).reason == "too_short"
    assert matcher.search_words(ayah_words(index, 67, 1)[:1]).status == "no_match"
    assert matcher.search("").status == "no_match"


def test_shuffled_words_do_not_match(index: QuranIndex, matcher: AyahMatcher) -> None:
    rng = random.Random(7)  # noqa: S311
    words = [index.words[rng.randrange(len(index.words))] for _ in range(14)]
    result = matcher.search_words(words)
    assert result.status == "no_match"
    assert result.reason == "low_confidence"
    assert result.best is None


def test_non_arabic_text_does_not_match(matcher: AyahMatcher) -> None:
    result = matcher.search("the quick brown fox jumps over the lazy dog 12345")
    assert result.status == "no_match"


def test_threshold_and_delta_are_respected(index: QuranIndex) -> None:
    words = ayah_words(index, 2, 255)[:12]
    strict = AyahMatcher(index, match_threshold=101, ambiguity_delta=2)
    assert strict.search_words(words).status == "no_match"
    loose = AyahMatcher(index, match_threshold=0, ambiguity_delta=100)
    assert loose.search_words(words).status == "ambiguous"  # everything is "close enough"
