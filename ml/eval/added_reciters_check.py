"""Check reciters whose gallery voice comes from mp3quran full-surah files.

Usage: uv run --project backend --group ml python ml/eval/added_reciters_check.py

These reciters have no per-ayah recordings, so the Phase 3 evaluation (which
uses per-ayah clips) cannot cover them. This check cuts 8-second queries from
surahs the gallery never saw (held-out surahs 36 and 67), clean and
phone-like, and applies the service's own decision rule and thresholds.

It also scores each reciter as a stranger, by removing them from the gallery:
any name returned then is a false accept.

Prints a table; writes nothing.
"""

import json
import sys
from pathlib import Path

import httpx
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO / "ml" / "eval"))

from app.core.system_certs import use_system_certs_if_requested

use_system_certs_if_requested()

from build_audio_eval import encode, phone_like

from app.audio.decode import SAMPLE_RATE, decode_audio
from app.core.config import Settings
from app.speaker.engine import OnnxSpeakerEngine
from app.speaker.gallery import Gallery

REGISTRY = REPO / "ml" / "registry" / "reciters.json"
CACHE = REPO / "ml" / "data" / "mp3quran"
QUERY_SURAHS = (36, 67)  # held out: never used to build the gallery
QUERIES_PER_SURAH = 12
QUERY_SEC = 8.0
SEED = 20261117


def queries(slug: str, server: str) -> list[np.ndarray]:
    clips = []
    window = int(QUERY_SEC * SAMPLE_RATE)
    with httpx.Client(timeout=300, follow_redirects=True) as client:
        for surah in QUERY_SURAHS:
            path = CACHE / slug / f"{surah:03d}.mp3"
            if not path.exists():
                response = client.get(f"{server}{surah:03d}.mp3")
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(response.content)
            audio = decode_audio(path.read_bytes(), max_bytes=512 * 1024 * 1024, max_seconds=7200)
            starts = np.linspace(
                20 * SAMPLE_RATE, len(audio) - 15 * SAMPLE_RATE - window, QUERIES_PER_SURAH
            )
            clips += [audio[int(s) : int(s) + window] for s in starts]
    return clips


def main() -> int:
    settings = Settings()
    floor, margin = settings.reciter_threshold, settings.reciter_min_margin
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    added = [r for r in registry if r["active"] and not r["sources"]["everyayah"]]
    gallery = Gallery.load(REPO / "ml" / "artifacts" / "gallery.npz")
    engine = OnnxSpeakerEngine(
        REPO / "ml" / "artifacts" / "speaker" / "resnet34.onnx", cpu_threads=4
    )
    rng = np.random.default_rng(SEED)

    sys.stdout.write(f"threshold {floor}, margin {margin}; {QUERY_SEC:.0f} s queries\n")
    sys.stdout.write(
        f"{'reciter':14}{'condition':10}{'n':>4}{'named right':>13}{'named wrong':>13}"
        f"{'unknown':>9}{'top-1 right':>13}{'as stranger: named':>20}\n"
    )
    for r in added:
        clips = queries(r["id"], r["sources"]["mp3quran_audio"][0]["server"])
        stranger_gallery = gallery.without_reciter(r["id"])
        for condition in ("clean", "phone"):
            right = wrong = unknown = top1 = accepted = 0
            for clip in clips:
                audio = clip
                if condition == "phone":
                    degraded, _ = phone_like(clip, rng)
                    coded = encode(degraded, "webm", "libopus", 20000)
                    audio = decode_audio(coded, max_bytes=10**8, max_seconds=60)
                embedding = engine.embed(audio)
                result = gallery.identify(embedding, floor, margin)
                top1 += gallery.rank(embedding)[0].reciter_id == r["id"]
                if result.status == "unknown" or result.best is None:
                    unknown += 1
                elif result.best.reciter_id == r["id"]:
                    right += 1
                else:
                    wrong += 1
                accepted += (
                    stranger_gallery.identify(embedding, floor, margin).status == "identified"
                )
            n = len(clips)
            sys.stdout.write(
                f"{r['id']:14}{condition:10}{n:>4}{right:>13}{wrong:>13}{unknown:>9}"
                f"{top1:>13}{accepted:>20}\n"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
