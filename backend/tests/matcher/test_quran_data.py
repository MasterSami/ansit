import re
import shutil
from pathlib import Path

import pytest

from app.matcher.normalize import tokenize
from app.matcher.quran_data import (
    METADATA_FILE,
    SIMPLE_FILE,
    UTHMANI_FILE,
    QuranData,
    QuranDataError,
    load_quran,
)


def test_counts(quran: QuranData) -> None:
    assert len(quran.surahs) == 114
    assert len(quran.ayahs) == 6236
    for surah in quran.surahs:
        assert sum(a.surah == surah.number for a in quran.ayahs) == surah.ayah_count


def test_basmala_is_a_numbered_ayah_only_in_fatiha(quran: QuranData) -> None:
    basmala = tokenize(quran.ayah(1, 1).text_simple)
    assert quran.ayah(1, 1).basmala_uthmani is None
    assert quran.ayah(9, 1).basmala_uthmani is None  # At-Tawba has no basmala
    assert tokenize(quran.ayah(9, 1).text_simple)[:4] != basmala

    for surah in quran.surahs:
        if surah.number in (1, 9):
            continue
        first = quran.ayah(surah.number, 1)
        assert first.basmala_uthmani is not None
        assert tokenize(first.basmala_uthmani) == basmala
        assert tokenize(first.text_simple)[:4] != basmala
        assert tokenize(first.text_uthmani)[:4] != basmala
    assert all(a.basmala_uthmani is None for a in quran.ayahs if a.ayah != 1)


def test_uthmani_text_is_verbatim_apart_from_the_basmala_split(
    quran: QuranData, data_dir: Path
) -> None:
    raw = {}
    for line in (data_dir / UTHMANI_FILE).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            surah, ayah, text = line.split("|", 2)
            raw[(int(surah), int(ayah))] = text
    for a in quran.ayahs:
        rebuilt = f"{a.basmala_uthmani} {a.text_uthmani}" if a.basmala_uthmani else a.text_uthmani
        assert rebuilt == raw[(a.surah, a.ayah)]


def test_metadata(quran: QuranData) -> None:
    assert (quran.ayah(1, 1).juz, quran.ayah(1, 1).page) == (1, 1)
    assert (quran.ayahs[-1].juz, quran.ayahs[-1].page) == (30, 604)
    # The example in the build brief: Al-Mulk 1 is juz 29, page 562, Meccan, 30 ayahs.
    mulk = quran.surah(67)
    assert (quran.ayah(67, 1).juz, quran.ayah(67, 1).page) == (29, 562)
    assert (mulk.revelation, mulk.ayah_count) == ("meccan", 30)
    assert quran.surah(2).revelation == "medinan"
    # juz and page never decrease through the mushaf
    for prev, cur in zip(quran.ayahs, quran.ayahs[1:], strict=False):
        assert cur.juz in (prev.juz, prev.juz + 1)
        assert cur.page in (prev.page, prev.page + 1)


def test_attribution_is_carried(quran: QuranData) -> None:
    assert "Tanzil" in quran.attribution
    assert "tanzil.net" in quran.attribution


def test_unknown_ayah_raises(quran: QuranData) -> None:
    with pytest.raises(KeyError):
        quran.ayah(1, 8)


# --- integrity failures must be loud ---


@pytest.fixture
def broken(data_dir: Path, tmp_path: Path) -> Path:
    for name in (SIMPLE_FILE, UTHMANI_FILE, METADATA_FILE):
        shutil.copy(data_dir / name, tmp_path / name)
    return tmp_path


def _rewrite(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    changed, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    assert count == 1, f"pattern {pattern!r} not found in {path.name}"
    path.write_text(changed, encoding="utf-8")


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(QuranDataError, match="missing"):
        load_quran(tmp_path)


def test_missing_ayah_is_detected(broken: Path) -> None:
    _rewrite(broken / SIMPLE_FILE, r"^2\|5\|.*\n", "")
    with pytest.raises(QuranDataError, match="6236"):
        load_quran(broken)


def test_wrong_per_surah_count_is_detected(broken: Path) -> None:
    # Same total, but an ayah moved from surah 2 to surah 3.
    _rewrite(broken / UTHMANI_FILE, r"^2\|286\|", "3|201|")
    with pytest.raises(QuranDataError, match="per-surah counts"):
        load_quran(broken)


def test_metadata_count_mismatch_is_detected(broken: Path) -> None:
    _rewrite(broken / METADATA_FILE, r'index="2" ayas="286"', 'index="2" ayas="285"')
    with pytest.raises(QuranDataError, match="6236"):
        load_quran(broken)


def test_missing_basmala_prefix_is_detected(broken: Path) -> None:
    _rewrite(broken / SIMPLE_FILE, r"^2\|1\|\S+ ", "2|1|")
    with pytest.raises(QuranDataError, match="basmala"):
        load_quran(broken)


def test_missing_copyright_block_is_detected(broken: Path) -> None:
    path = broken / UTHMANI_FILE
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(x for x in lines if not x.startswith("#")), encoding="utf-8")
    with pytest.raises(QuranDataError, match="copyright"):
        load_quran(broken)
