"""Build the reciter gallery: voice embeddings for every reciter in the registry.

Usage:
  uv run --project backend --group ml python ml/scripts/build_gallery.py  # everyone
  uv run --project backend --group ml python ml/scripts/build_gallery.py --reciter ID  # one

For each (reciter, style) it embeds about 60 ayahs from varied surahs, never
from the surahs held out for evaluation. Adding a reciter means adding them to
the registry and running this for that reciter; nothing is retrained.

Output: ml/artifacts/gallery.npz (embeddings only). The source audio is cached
under ml/data/ and is never stored in the gallery or committed.
"""

import argparse
import json
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO / "ml" / "eval"))

from build_audio_eval import encode, phone_like
from heldout import HELDOUT_SURAHS

from app.audio.decode import SAMPLE_RATE, AudioError, decode_audio
from app.matcher.quran_data import load_quran
from app.speaker.engine import EMBEDDING_DIM, OnnxSpeakerEngine
from app.speaker.gallery import Gallery, Voice

BASE_URL = "https://everyayah.com/data"
CACHE_DIR = REPO / "ml" / "data" / "everyayah"
REGISTRY = REPO / "ml" / "registry" / "reciters.json"
MODEL = REPO / "ml" / "artifacts" / "speaker" / "resnet34.onnx"
OUT = REPO / "ml" / "artifacts" / "gallery.npz"

SEED = 20261117
AYAHS_PER_VOICE = 60
MAX_PER_SURAH = 2
MIN_WORDS, MAX_WORDS = 10, 22  # long enough to give several seconds of voice
MIN_CLIP_SEC = 4.0
MAX_CLIP_SEC = 10.0  # about the length of a query; taken from the middle of the ayah
MIN_CLIPS = 30  # studio clips per voice, before phone-like copies


def gallery_ayahs() -> list[tuple[int, int]]:
    """The same ayahs for every voice: varied surahs, none held out for evaluation."""
    quran = load_quran(REPO / "ml" / "data" / "tanzil")
    pool = [
        (a.surah, a.ayah)
        for a in quran.ayahs
        if a.surah not in HELDOUT_SURAHS and MIN_WORDS <= len(a.text_simple.split()) <= MAX_WORDS
    ]
    random.Random(SEED).shuffle(pool)  # noqa: S311 - reproducible selection
    chosen: list[tuple[int, int]] = []
    per_surah: dict[int, int] = {}
    for surah, ayah in pool:
        if per_surah.get(surah, 0) < MAX_PER_SURAH:
            chosen.append((surah, ayah))
            per_surah[surah] = per_surah.get(surah, 0) + 1
        if len(chosen) == AYAHS_PER_VOICE:
            break
    return sorted(chosen)


def fetch(client: httpx.Client, folder: str, surah: int, ayah: int) -> Path | None:
    path = CACHE_DIR / folder / f"{surah:03d}{ayah:03d}.mp3"
    if path.exists() and path.stat().st_size > 0:
        return path
    response = client.get(f"{BASE_URL}/{folder}/{path.name}")
    if response.status_code == 404:
        return None  # some folders have gaps
    response.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    return path


def download(folder: str, ayahs: list[tuple[int, int]]) -> list[Path]:
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        return [p for s, a in ayahs if (p := fetch(client, folder, s, a)) is not None]


def embed_voice(
    engine: OnnxSpeakerEngine, files: list[Path], augment_seed: list[int] | None
) -> np.ndarray:
    """Embeddings of each clip and, if `augment_seed` is given, of a phone-like copy."""
    rng = np.random.default_rng(augment_seed) if augment_seed is not None else None
    rows = []
    for path in files:
        try:
            audio = decode_audio(path.read_bytes(), max_bytes=64 * 1024 * 1024, max_seconds=1800)
        except AudioError:
            continue
        if len(audio) < MIN_CLIP_SEC * SAMPLE_RATE:
            continue
        window = int(MAX_CLIP_SEC * SAMPLE_RATE)
        if len(audio) > window:
            start = (len(audio) - window) // 2
            audio = audio[start : start + window]
        rows.append(engine.embed(audio))
        if rng is not None:
            # A second view of the same clip as a phone would deliver it:
            # reverb, noise, band-limit, Opus. Without it, phone-like queries
            # score much lower against a studio-only gallery (Phase 3 report).
            degraded, _ = phone_like(audio, rng)
            kbps = int(rng.integers(16, 25))
            coded = encode(degraded, "webm", "libopus", kbps * 1000)
            rows.append(engine.embed(decode_audio(coded, max_bytes=10**8, max_seconds=60)))
    return np.stack(rows) if rows else np.zeros((0, EMBEDDING_DIM), dtype=np.float32)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reciter", action="append", help="only (re)build this reciter id")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument(
        "--no-augment", action="store_true", help="studio clips only, no phone-like copies"
    )
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    known = {r["id"] for r in registry}
    wanted = set(args.reciter or known)
    if wanted - known:
        raise SystemExit(f"not in the registry: {sorted(wanted - known)}")

    jobs = [
        (Voice(r["id"], src["style"]), src["folder"])
        for r in registry
        if r["active"] and r["id"] in wanted
        for src in r["sources"]["everyayah"]
    ]
    ayahs = gallery_ayahs()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        downloads = list(pool.map(lambda job: download(job[1], ayahs), jobs))

    engine = OnnxSpeakerEngine(MODEL, cpu_threads=4)
    built: dict[Voice, np.ndarray] = {}
    for (voice, folder), files in zip(jobs, downloads, strict=True):
        seed = None if args.no_augment else [SEED, *folder.encode()]
        vectors = embed_voice(engine, files, seed)
        if len(vectors) < MIN_CLIPS * (1 if args.no_augment else 2):
            raise SystemExit(f"{folder}: only {len(vectors)} usable clips (need {MIN_CLIPS})")
        built[voice] = vectors
        print(f"embedded  {voice.reciter_id:16} {voice.style:9} {len(vectors):3} clips  ({folder})")

    # Keep everything already in the gallery that was not rebuilt just now.
    if args.reciter and args.out.is_file():
        old = Gallery.load(args.out)
        for index, voice in enumerate(old.voices):
            if voice.reciter_id not in wanted:
                built.setdefault(voice, old.embeddings[old.voice_of_clip == index])

    voices = sorted(built, key=lambda v: (v.reciter_id, v.style))
    gallery = Gallery(
        voices,
        np.concatenate([built[v] for v in voices]),
        np.concatenate([np.full(len(built[v]), i, dtype=np.intp) for i, v in enumerate(voices)]),
    )
    gallery.save(args.out)
    reciters = len({v.reciter_id for v in voices})
    print(f"gallery   {reciters} reciters, {len(voices)} voices, {len(gallery.embeddings)} clips")
    print(f"wrote     {args.out.relative_to(REPO)}  ({args.out.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
