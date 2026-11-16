"""Fixtures that load the real Tanzil data. No Quran text is typed in the tests:
ayahs are referred to by (surah, ayah) and their text is read from the data."""

import os
from pathlib import Path

import pytest

from app.matcher.index import QuranIndex
from app.matcher.normalize import DEFAULT_CONFIG
from app.matcher.quran_data import SIMPLE_FILE, QuranData, load_quran
from app.matcher.search import AyahMatcher

REPO = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("ANSIT_QURAN_DATA_DIR", REPO / "ml" / "data" / "tanzil"))


@pytest.fixture(scope="session")
def data_dir() -> Path:
    if not (DATA_DIR / SIMPLE_FILE).is_file():
        message = f"Tanzil data not found in {DATA_DIR}; run `make data`"
        if os.environ.get("ANSIT_REQUIRE_QURAN_DATA") == "1":
            pytest.fail(message)  # CI must never silently skip these
        pytest.skip(message)
    return DATA_DIR


@pytest.fixture(scope="session")
def quran(data_dir: Path) -> QuranData:
    return load_quran(data_dir)


@pytest.fixture(scope="session")
def index(quran: QuranData) -> QuranIndex:
    return QuranIndex.build(quran, DEFAULT_CONFIG)


@pytest.fixture(scope="session")
def matcher(index: QuranIndex) -> AyahMatcher:
    return AyahMatcher(index, match_threshold=76, ambiguity_delta=2)
