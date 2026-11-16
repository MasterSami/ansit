"""Arabic text normalization for search.

The same function is applied to the Quran text when the index is built and to
ASR output at query time. It is an internal search form only: text shown to
users is always the unmodified Uthmani text.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

HamzaMode = Literal["keep", "drop", "merge_madd"]
Level = Literal["search", "diacritics"]

HAMZA = "ء"
ALEF = "ا"

# Tashkeel, dagger alef, Quranic annotation marks, tatweel, honorific signs.
_MARKS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")
# Anything that is not a base Arabic letter (hamza .. ya, minus tatweel).
_NON_LETTERS = re.compile("[^ء-غف-ي]+")

_FOLD = str.maketrans(
    {
        "أ": ALEF,  # alef with hamza above
        "إ": ALEF,  # alef with hamza below
        "آ": ALEF,  # alef with madda
        "ٱ": ALEF,  # alef wasla
        "ى": "ي",  # alef maksura -> ya
        "ة": "ه",  # ta marbuta -> ha
        "ؤ": "و",  # waw with hamza -> waw
        "ئ": "ي",  # ya with hamza -> ya
        "ی": "ي",  # Farsi ya -> ya
        "ک": "ك",  # keheh -> kaf
    }
)


@dataclass(frozen=True)
class NormalizationConfig:
    """`standalone_hamza`: what to do with a bare hamza (U+0621).

    - keep: leave it.
    - drop: remove every one.
    - merge_madd: remove it only when directly followed by alef, which is how the
      Uthmani script spells what the simple script writes as alef-with-madda.
    """

    standalone_hamza: HamzaMode = "merge_madd"


DEFAULT_CONFIG = NormalizationConfig()


def normalize_ar(
    text: str,
    level: Level = "search",
    config: NormalizationConfig = DEFAULT_CONFIG,
) -> str:
    """Normalize Arabic text.

    level="diacritics": only remove marks and collapse whitespace.
    level="search": also fold letter variants, drop punctuation/digits/non-Arabic.
    """
    text = unicodedata.normalize("NFKC", text)
    text = _MARKS.sub("", text)
    if level == "diacritics":
        return " ".join(text.split())

    text = text.translate(_FOLD)
    if config.standalone_hamza == "drop":
        text = text.replace(HAMZA, "")
    elif config.standalone_hamza == "merge_madd":
        text = text.replace(HAMZA + ALEF, ALEF)
    text = _NON_LETTERS.sub(" ", text)
    return " ".join(text.split())


def tokenize(text: str, config: NormalizationConfig = DEFAULT_CONFIG) -> list[str]:
    """Normalize at search level and split into words."""
    return normalize_ar(text, "search", config).split()
