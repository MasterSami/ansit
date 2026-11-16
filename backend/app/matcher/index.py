"""The Quran search index: one global word sequence plus n-gram postings.

Words are numbered globally across all ayahs and surahs, so a match can cross
ayah and surah boundaries.
"""

import gzip
import json
from array import array
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.matcher.normalize import NormalizationConfig, tokenize
from app.matcher.quran_data import (
    EXPECTED_AYAHS,
    EXPECTED_SURAHS,
    QuranData,
    QuranDataError,
    Surah,
)

FORMAT_VERSION = 1
DEFAULT_ARTIFACT = "quran_index.json.gz"


@dataclass(frozen=True)
class IndexedAyah:
    surah: int
    ayah: int
    words: tuple[str, ...]
    text_uthmani: str
    basmala_uthmani: str | None
    juz: int
    page: int


@dataclass(frozen=True)
class WordRef:
    """A word position as users see it (all 1-based)."""

    surah: int
    ayah: int
    word: int


@dataclass
class QuranIndex:
    config: NormalizationConfig
    surahs: tuple[Surah, ...]
    ayahs: tuple[IndexedAyah, ...]
    attribution: str

    # Derived in __post_init__ (rebuilt on load, not stored in the artifact).
    words: list[str] = field(init=False, repr=False)
    word_ayah: array[int] = field(init=False, repr=False)
    ayah_start: list[int] = field(init=False, repr=False)
    unigrams: dict[str, array[int]] = field(init=False, repr=False)
    bigrams: dict[str, array[int]] = field(init=False, repr=False)
    trigrams: dict[str, array[int]] = field(init=False, repr=False)
    duplicate_groups: dict[int, tuple[int, ...]] = field(init=False, repr=False)
    basmala_words: tuple[str, ...] = field(init=False)
    istiadha_words: tuple[str, ...] = field(init=False)

    def __post_init__(self) -> None:
        if len(self.surahs) != EXPECTED_SURAHS or len(self.ayahs) != EXPECTED_AYAHS:
            raise QuranDataError(
                f"index must hold 114 surahs / 6236 ayahs, "
                f"got {len(self.surahs)} / {len(self.ayahs)}"
            )

        self.words = []
        self.word_ayah = array("I")
        self.ayah_start = []
        for ayah_idx, ayah in enumerate(self.ayahs):
            self.ayah_start.append(len(self.words))
            self.words.extend(ayah.words)
            self.word_ayah.extend([ayah_idx] * len(ayah.words))

        uni: defaultdict[str, array[int]] = defaultdict(lambda: array("I"))
        bi: defaultdict[str, array[int]] = defaultdict(lambda: array("I"))
        tri: defaultdict[str, array[int]] = defaultdict(lambda: array("I"))
        words = self.words
        for pos in range(len(words)):
            uni[words[pos]].append(pos)
            if pos + 1 < len(words):
                bi[f"{words[pos]} {words[pos + 1]}"].append(pos)
            if pos + 2 < len(words):
                tri[f"{words[pos]} {words[pos + 1]} {words[pos + 2]}"].append(pos)
        self.unigrams, self.bigrams, self.trigrams = dict(uni), dict(bi), dict(tri)

        by_text: defaultdict[tuple[str, ...], list[int]] = defaultdict(list)
        for ayah_idx, ayah in enumerate(self.ayahs):
            by_text[ayah.words].append(ayah_idx)
        self.duplicate_groups = {
            member: tuple(group) for group in by_text.values() if len(group) > 1 for member in group
        }

        self._ayah_lookup = {(a.surah, a.ayah): i for i, a in enumerate(self.ayahs)}
        self.basmala_words = self.ayahs[self.ayah_index(1, 1)].words
        self.istiadha_words = self._derive_istiadha()

    def _derive_istiadha(self) -> tuple[str, ...]:
        """Assemble the isti'adha from Quran words, so it is never hand-typed.

        It is not an ayah. Its first word is word 2 of 113:1 (and of 114:1); the
        rest is the last four words of 16:98, the ayah that commands it.
        """
        falaq = self.ayahs[self.ayah_index(113, 1)].words
        nas = self.ayahs[self.ayah_index(114, 1)].words
        nahl = self.ayahs[self.ayah_index(16, 98)].words
        if len(falaq) < 2 or len(nas) < 2 or falaq[1] != nas[1] or len(nahl) < 4:
            raise QuranDataError("cannot derive the isti'adha from 113:1 / 114:1 / 16:98")
        return (falaq[1], *nahl[-4:])

    # --- lookups ---

    def ayah_index(self, surah: int, ayah: int) -> int:
        return self._ayah_lookup[(surah, ayah)]

    def word_ref(self, global_idx: int) -> WordRef:
        ayah_idx = self.word_ayah[global_idx]
        ayah = self.ayahs[ayah_idx]
        return WordRef(ayah.surah, ayah.ayah, global_idx - self.ayah_start[ayah_idx] + 1)

    def occurrences(self, start: int, end: int) -> list[int]:
        """Global start positions where words[start..end] (inclusive) occur verbatim."""
        seq = self.words[start : end + 1]
        length = len(seq)
        if length >= 3:
            postings = self.trigrams[" ".join(seq[:3])]
        elif length == 2:
            postings = self.bigrams[" ".join(seq)]
        else:
            postings = self.unigrams[seq[0]]
        words = self.words
        return [p for p in postings if words[p : p + length] == seq]

    # --- construction and persistence ---

    @classmethod
    def build(cls, quran: QuranData, config: NormalizationConfig) -> "QuranIndex":
        ayahs = []
        for a in quran.ayahs:
            words = tuple(tokenize(a.text_simple, config))
            if not words:
                raise QuranDataError(f"{a.surah}:{a.ayah} is empty after normalization")
            ayahs.append(
                IndexedAyah(
                    a.surah, a.ayah, words, a.text_uthmani, a.basmala_uthmani, a.juz, a.page
                )
            )
        return cls(config, quran.surahs, tuple(ayahs), quran.attribution)

    def save(self, path: Path) -> None:
        payload: dict[str, Any] = {
            "format_version": FORMAT_VERSION,
            "attribution": self.attribution,
            "normalization": asdict(self.config),
            "surahs": [asdict(s) for s in self.surahs],
            "ayahs": [
                [
                    a.surah,
                    a.ayah,
                    " ".join(a.words),
                    a.text_uthmani,
                    a.basmala_uthmani,
                    a.juz,
                    a.page,
                ]
                for a in self.ayahs
            ],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        # No timestamp and no file name in the gzip header: rebuilds are byte-identical.
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        with path.open("wb") as raw, gzip.GzipFile("", "wb", fileobj=raw, mtime=0) as fh:
            fh.write(data)

    @classmethod
    def load(cls, path: Path) -> "QuranIndex":
        if not path.is_file():
            raise QuranDataError(f"missing {path} - run `make index`")
        with gzip.open(path, "rb") as fh:
            payload = json.loads(fh.read().decode("utf-8"))
        if payload.get("format_version") != FORMAT_VERSION:
            raise QuranDataError(
                f"{path.name}: format {payload.get('format_version')} != {FORMAT_VERSION}; "
                "rebuild with `make index`"
            )
        return cls(
            config=NormalizationConfig(**payload["normalization"]),
            surahs=tuple(Surah(**s) for s in payload["surahs"]),
            ayahs=tuple(
                IndexedAyah(s, a, tuple(text.split()), uthmani, basmala, juz, page)
                for s, a, text, uthmani, basmala, juz, page in payload["ayahs"]
            ),
            attribution=payload["attribution"],
        )
