"""Download the Tanzil Quran text and metadata into ml/data/tanzil/.

Usage: uv run --project backend python ml/scripts/download_quran.py [--force]

Tanzil terms of use (CC BY 3.0): verbatim copies only, credit Tanzil Project and
link to tanzil.net. The files are stored exactly as served and never edited.
"""

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.core.system_certs import use_system_certs_if_requested

use_system_certs_if_requested()

from app.matcher.quran_data import METADATA_FILE, SIMPLE_FILE, UTHMANI_FILE, load_quran

DATA_DIR = REPO / "ml" / "data" / "tanzil"
TEXT_URL = "https://tanzil.net/pub/download/index.php"
SOURCES: dict[str, tuple[str, dict[str, str]]] = {
    SIMPLE_FILE: (TEXT_URL, {"quranType": "simple-clean", "outType": "txt-2", "agree": "true"}),
    UTHMANI_FILE: (TEXT_URL, {"quranType": "uthmani", "outType": "txt-2", "agree": "true"}),
    METADATA_FILE: ("https://tanzil.net/res/text/metadata/quran-data.xml", {}),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="re-download existing files")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict[str, str | int]] = {}
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        for name, (url, params) in SOURCES.items():
            path = DATA_DIR / name
            if path.exists() and not args.force:
                print(f"keep      {name}")
            else:
                response = client.get(url, params=params)
                response.raise_for_status()
                path.write_bytes(response.content)
                print(f"download  {name}  ({len(response.content):,} bytes)")
            content = path.read_bytes()
            manifest[name] = {
                "url": str(httpx.URL(url, params=params)),
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }

    quran = load_quran(DATA_DIR)  # integrity assertions; raises on any mismatch
    (DATA_DIR / "manifest.json").write_text(
        json.dumps(
            {"fetched_at": datetime.now(UTC).isoformat(timespec="seconds"), "files": manifest},
            indent=2,
        )
        + "\n"
    )
    print(f"verified  {len(quran.surahs)} surahs, {len(quran.ayahs)} ayahs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
