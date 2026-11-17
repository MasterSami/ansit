"""Build the Phase 2 audio evaluation set from EveryAyah per-ayah recordings.

Usage: uv run --project backend --group ml python ml/eval/build_audio_eval.py

For each reciter, consecutive ayahs from held-out surahs are concatenated and
random 5/8/12 s windows are cut from them, so windows start and end mid-ayah and
cross ayah boundaries. Each window is written twice: clean (WAV) and phone-like
(band-limited, reverberated, noisy, Opus 16-24 kbps in WebM).

Audio is cached under ml/data/ (gitignored) and never committed or redistributed.
"""

import argparse
import io
import json
import random
import sys
import wave
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

import av
import httpx
import numpy as np
from scipy import signal

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.core.system_certs import use_system_certs_if_requested

use_system_certs_if_requested()
sys.path.insert(0, str(REPO / "ml" / "eval"))

from heldout import EVAL_RECITERS, HELDOUT_SURAHS

from app.audio.decode import SAMPLE_RATE, Waveform, decode_audio
from app.matcher.quran_data import load_quran

BASE_URL = "https://everyayah.com/data"
CACHE_DIR = REPO / "ml" / "data" / "everyayah"
OUT_DIR = REPO / "ml" / "data" / "eval_audio"
SEED = 20261117

DURATIONS = (5, 8, 12)
RANDOM_PASSAGES = 6  # per reciter; each yields one window per duration
PREFIX_PASSAGES = 2  # per reciter; surah openings with isti'adha and/or basmala
PREFIX_DURATIONS = (8, 12)
MIN_PASSAGE_SEC = 30.0
MAX_PASSAGE_AYAHS = 14
NEGATIVE_CLIPS = 60


@dataclass
class Segment:
    """One source file inside a passage."""

    label: str  # "s:a", "istiadha" or "basmala"
    start: float
    end: float


@dataclass
class Clip:
    clip_id: str
    path: str
    reciter: str
    style: str
    condition: str  # clean | phone | negative
    kind: str  # random | prefix | silence | noise | tones
    duration: float
    overlaps: dict[str, float] = field(default_factory=dict)  # "s:a" -> seconds audible
    prefix: list[str] = field(default_factory=list)  # prefix parts audible >= 1 s
    snr_db: float | None = None
    opus_kbps: int | None = None


# ----------------------------------------------------------------- download


def fetch(client: httpx.Client, folder: str, name: str) -> Path:
    path = CACHE_DIR / folder / name
    if path.exists() and path.stat().st_size > 0:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    response = client.get(f"{BASE_URL}/{folder}/{name}")
    response.raise_for_status()
    path.write_bytes(response.content)
    return path


def load(path: Path) -> Waveform:
    return decode_audio(path.read_bytes(), max_bytes=64 * 1024 * 1024, max_seconds=1800)


# --------------------------------------------------------------- degradation


def pink_noise(n: int, rng: np.random.Generator) -> Waveform:
    spectrum = np.fft.rfft(rng.standard_normal(n))
    freqs = np.fft.rfftfreq(n)
    spectrum[1:] /= np.sqrt(freqs[1:])
    spectrum[0] = 0
    noise = np.fft.irfft(spectrum, n)
    return (noise / (np.std(noise) + 1e-9)).astype(np.float32)


def phone_like(clean: Waveform, rng: np.random.Generator) -> tuple[Waveform, float]:
    """Room reverb -> background noise at 10-20 dB SNR -> phone band-limit."""
    rt60 = rng.uniform(0.25, 0.6)
    taps = int(rt60 * SAMPLE_RATE)
    decay = np.exp(-6.9 * np.arange(taps) / taps)  # -60 dB at rt60
    impulse = rng.standard_normal(taps) * decay * rng.uniform(0.15, 0.35)
    impulse[0] = 1.0
    wet = signal.fftconvolve(clean, impulse)[: len(clean)]

    snr_db = float(rng.uniform(10, 20))
    speech_rms = float(np.sqrt(np.mean(wet**2)) + 1e-9)
    noise = pink_noise(len(wet), rng) * speech_rms / (10 ** (snr_db / 20))
    noisy = wet + noise

    sos = signal.butter(4, [250, 3600], btype="bandpass", fs=SAMPLE_RATE, output="sos")
    out = signal.sosfilt(sos, noisy)
    peak = float(np.max(np.abs(out)) + 1e-9)
    return (out / peak * 0.7).astype(np.float32), snr_db


# ------------------------------------------------------------------ encoding


def write_wav(path: Path, waveform: Waveform) -> None:
    pcm = (np.clip(waveform, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(SAMPLE_RATE)
        fh.writeframes(pcm.tobytes())


def encode(waveform: Waveform, container_format: str, codec: str, bitrate: int) -> bytes:
    """Encode with PyAV (no ffmpeg binary needed). Also used by the backend tests."""
    pcm = (np.clip(waveform, -1, 1) * 32767).astype(np.int16)
    buffer = io.BytesIO()
    with av.open(buffer, mode="w", format=container_format) as container:
        rate = 48_000 if codec == "libopus" else SAMPLE_RATE
        stream = container.add_stream(codec, rate=rate)
        stream.bit_rate = bitrate
        stream.layout = "mono"
        resampler = av.AudioResampler(format=stream.format.name, layout="mono", rate=rate)
        frame = av.AudioFrame.from_ndarray(pcm.reshape(1, -1), format="s16", layout="mono")
        frame.sample_rate = SAMPLE_RATE
        fifo = av.AudioFifo()
        for resampled in resampler.resample(frame):
            fifo.write(resampled)
        for resampled in resampler.resample(None):
            fifo.write(resampled)
        size = stream.frame_size or 960
        while fifo.samples >= size:
            for packet in stream.encode(fifo.read(size)):
                container.mux(packet)
        if fifo.samples:
            for packet in stream.encode(fifo.read(fifo.samples)):
                container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)
    return buffer.getvalue()


# ------------------------------------------------------------------ building


def build_passage(
    client: httpx.Client,
    folder: str,
    ayah_counts: dict[int, int],
    rng: random.Random,
    prefix: tuple[str, ...] | None,
) -> tuple[Waveform, list[Segment]]:
    """Concatenate consecutive ayahs (optionally preceded by isti'adha/basmala)."""
    for _ in range(10):  # a folder may lack the first file of a draw; draw again
        passage, segments = _draw_passage(client, folder, ayah_counts, rng, prefix)
        if any(":" in seg.label for seg in segments):
            return passage, segments
    raise RuntimeError(f"{folder}: no usable passage after 10 draws")


def _draw_passage(
    client: httpx.Client,
    folder: str,
    ayah_counts: dict[int, int],
    rng: random.Random,
    prefix: tuple[str, ...] | None,
) -> tuple[Waveform, list[Segment]]:
    surah = rng.choice(HELDOUT_SURAHS)
    first = 1 if prefix is not None else rng.randint(1, max(1, ayah_counts[surah] - 4))
    parts: list[tuple[str, Waveform]] = []
    for name in prefix or ():
        # Not every folder ships these two files. The basmala can always be
        # taken from 1:1 by the same reciter; a missing isti'adha is skipped.
        candidates = ["audhubillah.mp3"] if name == "istiadha" else ["bismillah.mp3", "001001.mp3"]
        for file in candidates:
            try:
                parts.append((name, load(fetch(client, folder, file))))
                break
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code != 404:
                    raise

    ayah, total = first, 0.0
    while ayah <= ayah_counts[surah] and ayah - first < MAX_PASSAGE_AYAHS:
        try:
            audio = load(fetch(client, folder, f"{surah:03d}{ayah:03d}.mp3"))
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 404:
                raise
            # Some folders have gaps. End the passage here; windows longer than
            # what was collected are simply not cut.
            print(f"missing   {folder}/{surah:03d}{ayah:03d}.mp3")
            break
        parts.append((f"{surah}:{ayah}", audio))
        total += len(audio) / SAMPLE_RATE
        ayah += 1
        if total >= MIN_PASSAGE_SEC:
            break

    segments, cursor = [], 0.0
    for label, audio in parts:
        length = len(audio) / SAMPLE_RATE
        segments.append(Segment(label, cursor, cursor + length))
        cursor += length
    if not parts:
        return np.zeros(0, dtype=np.float32), []
    return np.concatenate([audio for _, audio in parts]), segments


def build_reciter(folder: str, style: str, ayah_counts: dict[int, int]) -> list[Clip]:
    rng = random.Random(f"{SEED}:{folder}")  # noqa: S311 - reproducible eval set
    np_rng = np.random.default_rng([SEED, *folder.encode()])
    out_dir = OUT_DIR / "clips" / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    clips: list[Clip] = []

    plans: list[tuple[str, tuple[str, ...] | None, tuple[int, ...]]] = [
        ("random", None, DURATIONS) for _ in range(RANDOM_PASSAGES)
    ]
    plans += [
        ("prefix", ("istiadha", "basmala"), PREFIX_DURATIONS),
        ("prefix", ("basmala",), PREFIX_DURATIONS),
    ][:PREFIX_PASSAGES]

    with httpx.Client(timeout=60, follow_redirects=True) as client:
        for number, (kind, prefix, durations) in enumerate(plans):
            passage, segments = build_passage(client, folder, ayah_counts, rng, prefix)
            total = len(passage) / SAMPLE_RATE
            for duration in durations:
                if total < duration:
                    continue
                offset = 0.0 if kind == "prefix" else rng.uniform(0, total - duration)
                window = passage[int(offset * SAMPLE_RATE) : int((offset + duration) * SAMPLE_RATE)]
                overlaps, audible_prefix = {}, []
                for seg in segments:
                    shared = min(seg.end, offset + duration) - max(seg.start, offset)
                    if shared <= 0:
                        continue
                    if ":" in seg.label:
                        overlaps[seg.label] = round(shared, 3)
                    elif shared >= 1.0:
                        audible_prefix.append(seg.label)

                stem = f"{number:02d}_{kind}_{duration:02d}s"
                clean_path = out_dir / f"{stem}_clean.wav"
                write_wav(clean_path, window)
                degraded, snr_db = phone_like(window, np_rng)
                kbps = int(np_rng.integers(16, 25))
                phone_path = out_dir / f"{stem}_phone.webm"
                phone_path.write_bytes(encode(degraded, "webm", "libopus", kbps * 1000))

                for condition, path, snr, rate in (
                    ("clean", clean_path, None, None),
                    ("phone", phone_path, snr_db, kbps),
                ):
                    clips.append(
                        Clip(
                            clip_id=f"{folder}/{path.name}",
                            path=str(path.relative_to(OUT_DIR)),
                            reciter=folder,
                            style=style,
                            condition=condition,
                            kind=kind,
                            duration=float(duration),
                            overlaps=overlaps,
                            prefix=audible_prefix,
                            snr_db=snr,
                            opus_kbps=rate,
                        )
                    )
    return clips


def build_negatives() -> list[Clip]:
    """Non-speech clips that must come back as no_match."""
    rng = np.random.default_rng(SEED)
    out_dir = OUT_DIR / "clips" / "_negative"
    out_dir.mkdir(parents=True, exist_ok=True)
    clips = []
    n = 8 * SAMPLE_RATE
    t = np.arange(n) / SAMPLE_RATE
    for i in range(NEGATIVE_CLIPS):
        kind = ("silence", "noise", "tones")[i % 3]
        if kind == "silence":
            audio = (rng.standard_normal(n) * 1e-4).astype(np.float32)
        elif kind == "noise":
            audio = pink_noise(n, rng) * float(rng.uniform(0.02, 0.2))
        else:  # a slowly changing chord, music-like
            audio = np.zeros(n, dtype=np.float32)
            for freq in rng.uniform(110, 880, size=4):
                audio += np.sin(2 * np.pi * freq * t + rng.uniform(0, 6.28)).astype(np.float32)
            audio *= (0.15 * (1 + 0.5 * np.sin(2 * np.pi * 0.7 * t))).astype(np.float32)
        path = out_dir / f"{i:02d}_{kind}.wav"
        write_wav(path, audio)
        clips.append(
            Clip(
                clip_id=f"_negative/{path.name}",
                path=str(path.relative_to(OUT_DIR)),
                reciter="",
                style="",
                condition="negative",
                kind=kind,
                duration=8.0,
            )
        )
    return clips


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    quran = load_quran(REPO / "ml" / "data" / "tanzil")
    ayah_counts = {s.number: s.ayah_count for s in quran.surahs}

    clips: list[Clip] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = {
            folder: pool.submit(build_reciter, folder, style, ayah_counts)
            for folder, style in EVAL_RECITERS.items()
        }
        for folder, job in jobs.items():
            built = job.result()
            clips.extend(built)
            print(f"built     {folder}: {len(built)} clips")
    clips.extend(build_negatives())

    manifest = OUT_DIR / "manifest.jsonl"
    manifest.write_text("".join(json.dumps(asdict(c), ensure_ascii=False) + "\n" for c in clips))
    cached = sum(f.stat().st_size for f in CACHE_DIR.rglob("*.mp3"))
    print(f"clips     {len(clips)}  ({len(EVAL_RECITERS)} reciters)")
    where = CACHE_DIR.relative_to(REPO)
    print(f"source    {cached / 1e6:.0f} MB of EveryAyah audio cached in {where}")
    print(f"wrote     {manifest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
