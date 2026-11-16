"""Build the Quran search index artifact from the downloaded Tanzil files.

Usage: uv run --project backend python ml/scripts/build_index.py [--hamza MODE]
"""

import argparse
import sys
import time
from pathlib import Path
from typing import get_args

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.matcher.index import DEFAULT_ARTIFACT, QuranIndex
from app.matcher.normalize import DEFAULT_CONFIG, HamzaMode, NormalizationConfig
from app.matcher.quran_data import load_quran

DATA_DIR = REPO / "ml" / "data" / "tanzil"
ARTIFACT = REPO / "ml" / "artifacts" / DEFAULT_ARTIFACT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--hamza", choices=get_args(HamzaMode), default=DEFAULT_CONFIG.standalone_hamza
    )
    parser.add_argument("--out", type=Path, default=ARTIFACT)
    args = parser.parse_args()

    index = QuranIndex.build(load_quran(DATA_DIR), NormalizationConfig(args.hamza))
    index.save(args.out)

    started = time.perf_counter()
    loaded = QuranIndex.load(args.out)
    load_ms = (time.perf_counter() - started) * 1000
    if loaded.words != index.words:
        raise SystemExit("artifact round-trip mismatch")

    groups = set(index.duplicate_groups.values())
    print(f"wrote     {args.out.relative_to(REPO)}  ({args.out.stat().st_size:,} bytes)")
    print(f"hamza     {args.hamza}")
    print(f"words     {len(index.words):,}  (vocabulary {len(index.unigrams):,})")
    print(f"n-grams   {len(index.bigrams):,} bigrams, {len(index.trigrams):,} trigrams")
    print(f"dup       {len(groups)} groups, largest {max(len(g) for g in groups)} ayahs")
    print(f"load      {load_ms:.0f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
