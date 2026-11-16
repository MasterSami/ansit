"""Loads the Tanzil Quran text and metadata, with integrity checks.

Every ayah string in the system comes from here; nothing is hand-typed.

Files expected in the data directory (see `ml/scripts/download_quran.py`):
  quran-simple-clean.txt   search text
  quran-uthmani.txt        display text (shown verbatim)
  quran-data.xml           surah / juz / page metadata
"""

import bisect
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.matcher.normalize import NormalizationConfig, tokenize

SIMPLE_FILE = "quran-simple-clean.txt"
UTHMANI_FILE = "quran-uthmani.txt"
METADATA_FILE = "quran-data.xml"

EXPECTED_SURAHS = 114
EXPECTED_AYAHS = 6236
EXPECTED_JUZ = 30
EXPECTED_PAGES = 604
FATIHA = 1
TAWBA = 9  # the only surah recited without a basmala

Revelation = Literal["meccan", "medinan"]

# Prefix comparison must not depend on the configurable hamza rule.
_STRICT = NormalizationConfig(standalone_hamza="keep")


class QuranDataError(RuntimeError):
    """The source data is missing or does not have the expected shape."""


@dataclass(frozen=True)
class Surah:
    number: int
    name_ar: str
    name_en: str
    ayah_count: int
    revelation: Revelation


@dataclass(frozen=True)
class Ayah:
    surah: int
    ayah: int
    text_simple: str
    """Search text, without the basmala prefix."""
    text_uthmani: str
    """Display text, verbatim from Tanzil, without the basmala prefix."""
    basmala_uthmani: str | None
    """The basmala Tanzil embeds before ayah 1, verbatim. None for other ayahs."""
    juz: int
    page: int


@dataclass(frozen=True)
class QuranData:
    surahs: tuple[Surah, ...]
    ayahs: tuple[Ayah, ...]
    attribution: str
    """Tanzil's copyright block; must accompany anything derived from the text."""

    def surah(self, number: int) -> Surah:
        return self.surahs[number - 1]

    def ayah(self, surah: int, ayah: int) -> Ayah:
        found = self._lookup().get((surah, ayah))
        if found is None:
            raise KeyError(f"no ayah {surah}:{ayah}")
        return found

    def _lookup(self) -> dict[tuple[int, int], Ayah]:
        cache: dict[tuple[int, int], Ayah] | None = self.__dict__.get("_by_ref")
        if cache is None:
            cache = {(a.surah, a.ayah): a for a in self.ayahs}
            object.__setattr__(self, "_by_ref", cache)
        return cache


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise QuranDataError(message)


def _read_text_file(path: Path) -> tuple[list[tuple[int, int, str]], str]:
    """Returns (rows, copyright block)."""
    _require(path.is_file(), f"missing {path} - run `make data`")
    rows: list[tuple[int, int, str]] = []
    notice: list[str] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            notice.append(line)
            continue
        parts = line.split("|", 2)
        _require(len(parts) == 3, f"{path.name}:{line_no}: expected surah|ayah|text")
        _require(bool(parts[2].strip()), f"{path.name}:{line_no}: empty ayah text")
        rows.append((int(parts[0]), int(parts[1]), parts[2].strip()))
    _require(bool(notice), f"{path.name}: Tanzil copyright block is missing")
    return rows, "\n".join(notice)


def _read_metadata(path: Path) -> tuple[list[Surah], list[tuple[int, int]], list[tuple[int, int]]]:
    """Returns (surahs, juz starts, page starts); starts are (surah, ayah)."""
    _require(path.is_file(), f"missing {path} - run `make data`")
    raw = path.read_text(encoding="utf-8")
    _require("<!DOCTYPE" not in raw and "<!ENTITY" not in raw, f"{path.name}: unexpected DTD")
    root = ET.fromstring(raw)  # noqa: S314 - DTD/entities rejected above

    surahs: list[Surah] = []
    for node in root.iterfind("./suras/sura"):
        kind = node.attrib["type"].lower()
        _require(kind in ("meccan", "medinan"), f"unknown revelation type {kind!r}")
        surahs.append(
            Surah(
                number=int(node.attrib["index"]),
                name_ar=node.attrib["name"],
                name_en=node.attrib["tname"],
                ayah_count=int(node.attrib["ayas"]),
                revelation="meccan" if kind == "meccan" else "medinan",
            )
        )

    def starts(xpath: str) -> list[tuple[int, int]]:
        return [(int(n.attrib["sura"]), int(n.attrib["aya"])) for n in root.iterfind(xpath)]

    return surahs, starts("./juzs/juz"), starts("./pages/page")


def _split_basmala(text: str, basmala_words: list[str], where: str) -> tuple[str, str]:
    """Split `text` into (basmala prefix, rest), verifying the prefix by normalized words."""
    tokens = text.split()
    count = len(basmala_words)
    prefix, rest = tokens[:count], tokens[count:]
    _require(
        tokenize(" ".join(prefix), _STRICT) == basmala_words,
        f"{where}: expected a basmala prefix, found {' '.join(prefix)!r}",
    )
    _require(bool(rest), f"{where}: nothing left after the basmala")
    return " ".join(prefix), " ".join(rest)


def load_quran(data_dir: Path) -> QuranData:
    """Load and verify. Raises QuranDataError on any integrity failure."""
    simple_rows, _ = _read_text_file(data_dir / SIMPLE_FILE)
    uthmani_rows, attribution = _read_text_file(data_dir / UTHMANI_FILE)
    surahs, juz_starts, page_starts = _read_metadata(data_dir / METADATA_FILE)

    # --- metadata shape ---
    _require(len(surahs) == EXPECTED_SURAHS, f"expected 114 surahs, metadata has {len(surahs)}")
    _require(
        [s.number for s in surahs] == list(range(1, EXPECTED_SURAHS + 1)),
        "surah numbers are not 1..114 in order",
    )
    _require(
        sum(s.ayah_count for s in surahs) == EXPECTED_AYAHS,
        "metadata ayah counts do not sum to 6236",
    )
    _require(len(juz_starts) == EXPECTED_JUZ, f"expected 30 juz, found {len(juz_starts)}")
    _require(len(page_starts) == EXPECTED_PAGES, f"expected 604 pages, found {len(page_starts)}")
    _require(juz_starts == sorted(juz_starts) and juz_starts[0] == (1, 1), "juz starts malformed")
    _require(
        page_starts == sorted(page_starts) and page_starts[0] == (1, 1), "page starts malformed"
    )

    # --- text shape: both files hold exactly the ayahs the metadata promises ---
    expected_refs = [(s.number, a) for s in surahs for a in range(1, s.ayah_count + 1)]
    for name, rows in ((SIMPLE_FILE, simple_rows), (UTHMANI_FILE, uthmani_rows)):
        _require(len(rows) == EXPECTED_AYAHS, f"{name}: expected 6236 ayahs, found {len(rows)}")
        _require(
            [(s, a) for s, a, _ in rows] == expected_refs,
            f"{name}: ayah numbering does not match per-surah counts in the metadata",
        )

    # --- basmala: a numbered ayah only in Al-Fatiha ---
    basmala_words = tokenize(simple_rows[0][2], _STRICT)
    _require(
        tokenize(uthmani_rows[0][2], _STRICT) == basmala_words,
        "1:1 differs between the simple and Uthmani files after normalization",
    )

    ayahs: list[Ayah] = []
    for (surah, ayah, simple), (_, _, uthmani) in zip(simple_rows, uthmani_rows, strict=True):
        ref = (surah, ayah)
        basmala: str | None = None
        if ayah == 1 and surah not in (FATIHA, TAWBA):
            _, simple = _split_basmala(simple, basmala_words, f"{SIMPLE_FILE} {surah}:1")
            basmala, uthmani = _split_basmala(uthmani, basmala_words, f"{UTHMANI_FILE} {surah}:1")
        ayahs.append(
            Ayah(
                surah=surah,
                ayah=ayah,
                text_simple=simple,
                text_uthmani=uthmani,
                basmala_uthmani=basmala,
                juz=bisect.bisect_right(juz_starts, ref),
                page=bisect.bisect_right(page_starts, ref),
            )
        )

    _require(ayahs[-1].juz == EXPECTED_JUZ, "last ayah is not in juz 30")
    _require(ayahs[-1].page == EXPECTED_PAGES, "last ayah is not on page 604")
    return QuranData(surahs=tuple(surahs), ayahs=tuple(ayahs), attribution=attribution)
