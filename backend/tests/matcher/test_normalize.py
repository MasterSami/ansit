import re

import pytest

from app.matcher.normalize import NormalizationConfig, normalize_ar, tokenize
from app.matcher.quran_data import QuranData

# Synthetic strings built from code points (not Quran text).
BA, TA, LAM, MIM, ALEF, HAMZA = "ب", "ت", "ل", "م", "ا", "ء"
FATHA, SHADDA, SUKUN, DAGGER_ALEF, TATWEEL = "َ", "ّ", "ْ", "ٰ", "ـ"
SMALL_HIGH_LIGATURE, HONORIFIC = "ۖ", "ؐ"

LETTERS_ONLY = re.compile("^[ء-غف-ي ]*$")


def test_removes_marks() -> None:
    marked = (
        BA + FATHA + TATWEEL + LAM + SHADDA + DAGGER_ALEF + MIM + SUKUN + SMALL_HIGH_LIGATURE
    ) + HONORIFIC
    assert normalize_ar(marked) == BA + LAM + MIM


@pytest.mark.parametrize(
    ("variant", "folded"),
    [
        ("أ", ALEF),  # alef hamza above
        ("إ", ALEF),  # alef hamza below
        ("آ", ALEF),  # alef madda
        ("ٱ", ALEF),  # alef wasla
        ("ى", "ي"),  # alef maksura
        ("ة", "ه"),  # ta marbuta
        ("ؤ", "و"),  # waw hamza
        ("ئ", "ي"),  # ya hamza
    ],
)
def test_folds_letter_variants(variant: str, folded: str) -> None:
    assert normalize_ar(BA + variant) == BA + folded


def test_strips_punctuation_digits_and_non_arabic() -> None:
    text = f"  {BA}{LAM}, 12 ١٢ abc {MIM}{TA}، ؟\n{LAM}{MIM}. "
    assert normalize_ar(text) == f"{BA}{LAM} {MIM}{TA} {LAM}{MIM}"


def test_standalone_hamza_modes() -> None:
    word = MIM + HAMZA + ALEF + BA + HAMZA  # hamza before alef, and a final hamza
    assert normalize_ar(word, config=NormalizationConfig("keep")) == word
    assert normalize_ar(word, config=NormalizationConfig("drop")) == MIM + ALEF + BA
    assert normalize_ar(word, config=NormalizationConfig("merge_madd")) == MIM + ALEF + BA + HAMZA


def test_diacritics_level_keeps_letter_forms() -> None:
    text = "أ" + FATHA + BA + "  " + TA + "ة"
    assert normalize_ar(text, level="diacritics") == "أ" + BA + " " + TA + "ة"


def test_empty_and_whitespace() -> None:
    assert normalize_ar("") == ""
    assert normalize_ar(" \t\n ") == ""
    assert tokenize("...") == []


# --- on the real data ---


def test_every_ayah_normalizes_to_letters_and_single_spaces(quran: QuranData) -> None:
    for ayah in quran.ayahs:
        for text in (ayah.text_simple, ayah.text_uthmani):
            out = normalize_ar(text)
            assert out, f"{ayah.surah}:{ayah.ayah} normalized to nothing"
            assert LETTERS_ONLY.match(out)
            assert "  " not in out and out == out.strip()


def test_idempotent_on_every_ayah(quran: QuranData) -> None:
    for ayah in quran.ayahs:
        once = normalize_ar(ayah.text_uthmani)
        assert normalize_ar(once) == once


def test_uthmani_and_simple_basmala_normalize_identically(quran: QuranData) -> None:
    fatiha = quran.ayah(1, 1)
    assert tokenize(fatiha.text_uthmani) == tokenize(fatiha.text_simple)
    # Surahs 95 and 97 spell the basmala with a shadda on the first letter.
    for surah in (2, 95, 97):
        basmala = quran.ayah(surah, 1).basmala_uthmani
        assert basmala is not None
        assert tokenize(basmala) == tokenize(fatiha.text_simple)


def test_uthmani_madd_spelling_matches_simple_under_merge_madd(quran: QuranData) -> None:
    """Uthmani writes hamza+alef where simple writes alef-madda; only `keep` splits them."""
    hamza_alef = HAMZA + FATHA + ALEF
    sample = next(
        a for a in quran.ayahs if hamza_alef in a.text_uthmani and len(a.text_simple) < 80
    )
    word_no = next(i for i, w in enumerate(sample.text_uthmani.split()) if hamza_alef in w)
    uthmani_word = sample.text_uthmani.split()[word_no]
    keep, merge = NormalizationConfig("keep"), NormalizationConfig("merge_madd")
    assert HAMZA in normalize_ar(uthmani_word, config=keep)
    assert normalize_ar(uthmani_word, config=merge).startswith(
        normalize_ar(uthmani_word, config=keep).split(HAMZA)[0] + ALEF
    )
    assert HAMZA + ALEF not in normalize_ar(uthmani_word, config=merge)
