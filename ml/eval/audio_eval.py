"""Phase 2 end-to-end evaluation: audio clip -> decode -> VAD -> ASR -> ayah match.

Usage:
  uv run --project backend python ml/eval/audio_eval.py run [--models NAME ...]
  uv run --project backend python ml/eval/audio_eval.py report

`run` stores raw per-clip results under ml/data/eval_audio/results/ (gitignored;
they contain transcripts). `report` turns them into ml/eval/reports/phase2.md.
Every number in the report comes from those runs.
"""

import argparse
import json
import os
import platform
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.asr.faster_whisper_engine import FasterWhisperEngine
from app.asr.guards import GuardConfig
from app.audio.decode import AudioError
from app.audio.vad import SpeechDetector
from app.core.config import Settings
from app.matcher.index import DEFAULT_ARTIFACT, QuranIndex
from app.matcher.search import AyahMatcher
from app.pipeline import AudioLimits, AyahIdentifier

EVAL_DIR = REPO / "ml" / "data" / "eval_audio"
RESULTS_DIR = EVAL_DIR / "results"
MODELS_DIR = REPO / "ml" / "artifacts" / "asr"
REPORT = REPO / "ml" / "eval" / "reports" / "phase2.md"

PRIMARY_MODEL = "tarteel-base"
COMPARISON_MODELS = ("tarteel-tiny", "deepdml-small")
CPU_THREADS = 4
AUDIBLE_SEC = 1.0  # an ayah counts as "in the clip" if at least this much is heard
TARGET_TOP1 = 0.90
TARGET_P95_MS = 2500
WORST = "Abdullaah_3awwaad_Al-Juhaynee_128kbps"


def load_manifest() -> list[dict[str, Any]]:
    path = EVAL_DIR / "manifest.jsonl"
    if not path.is_file():
        raise SystemExit(f"missing {path} - run ml/eval/build_audio_eval.py")
    return [json.loads(line) for line in path.read_text().splitlines()]


def in_comparison_subset(clip: dict[str, Any]) -> bool:
    """The other models only run on 8 s clips, to bound CPU time."""
    return clip["duration"] == 8.0


# ----------------------------------------------------------------------- run


def run_model(name: str, clips: list[dict[str, Any]], settings: Settings) -> None:
    index = QuranIndex.load(REPO / "ml" / "artifacts" / DEFAULT_ARTIFACT)
    identifier = AyahIdentifier(
        asr=FasterWhisperEngine(
            MODELS_DIR / name,
            device="cpu",
            compute_type="int8",
            cpu_threads=CPU_THREADS,
            beam_size=settings.asr_beam_size,
        ),
        matcher=AyahMatcher(index, settings.match_threshold, settings.ambiguity_delta),
        vad=SpeechDetector(threshold=settings.vad_threshold),
        limits=AudioLimits(
            max_upload_bytes=int(settings.max_upload_mb * 1024 * 1024),
            min_clip_sec=settings.min_clip_sec,
            max_clip_sec=settings.max_clip_sec,
            min_speech_sec=settings.min_speech_sec,
            trim_silence=settings.vad_trim_silence,
        ),
        guards=GuardConfig(
            max_no_speech_prob=settings.asr_max_no_speech_prob,
            min_avg_logprob=settings.asr_min_avg_logprob,
            max_compression_ratio=settings.asr_max_compression_ratio,
        ),
    )
    identifier.asr.warm_up()  # type: ignore[attr-defined]
    identifier.vad.warm_up()

    def ref(ayah_idx: int) -> str:
        ayah = index.ayahs[ayah_idx]
        return f"{ayah.surah}:{ayah.ayah}"

    results = []
    started = time.perf_counter()
    for number, clip in enumerate(clips, 1):
        data = (EVAL_DIR / clip["path"]).read_bytes()
        row: dict[str, Any] = {"clip_id": clip["clip_id"], "bytes": len(data)}
        try:
            out = identifier.identify(data)
        except AudioError as exc:
            row.update(status="error", reason=exc.reason)
            results.append(row)
            continue
        match = out.match
        row.update(
            status=out.status,
            reason=out.reason,
            guard_flags=out.guard_flags,
            speech_sec=round(out.speech_sec, 2),
            timings_ms={k: round(v, 1) for k, v in out.timings_ms.items()},
            best=ref(match.best.ayah_idx) if match and match.best else None,
            score=round(match.best.score, 1) if match and match.best else None,
            ranked=[ref(c.ayah_idx) for c in match.ranked[:3]] if match else [],
            alternatives=[ref(c.ayah_idx) for c in match.alternatives] if match else [],
            repeated_count=match.repeated_count if match else None,
            prefix_detected=match.prefix_detected if match else None,
            avg_logprob=round(out.asr.avg_logprob, 3) if out.asr else None,
            no_speech_prob=round(out.asr.no_speech_prob, 3) if out.asr else None,
            transcript=out.asr.text if out.asr else None,
        )
        results.append(row)
        if number % 100 == 0:
            rate = (time.perf_counter() - started) / number
            print(f"{name}: {number}/{len(clips)}  ({rate:.2f} s/clip)", flush=True)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": name,
        "source": json.loads((MODELS_DIR / name / "SOURCE.json").read_text()),
        "cpu_threads": CPU_THREADS,
        "beam_size": settings.asr_beam_size,
        "match_threshold": settings.match_threshold,
        "ambiguity_delta": settings.ambiguity_delta,
        "vad_threshold": settings.vad_threshold,
        "vad_trim_silence": settings.vad_trim_silence,
        "machine": f"{platform.machine()}, {os.cpu_count()} logical CPUs",
        "python": platform.python_version(),
        "results": results,
    }
    (RESULTS_DIR / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False))
    print(f"{name}: done, {len(results)} clips in {time.perf_counter() - started:.0f} s")


# -------------------------------------------------------------------- report


def pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "n/a"


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))] if ordered else float("nan")


def table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


class Scored:
    """One clip's result joined with its ground truth."""

    def __init__(self, clip: dict[str, Any], row: dict[str, Any]) -> None:
        self.clip, self.row = clip, row
        overlaps: dict[str, float] = clip["overlaps"]
        self.audible = {ref for ref, sec in overlaps.items() if sec >= AUDIBLE_SEC}
        self.main = max(overlaps, key=lambda r: overlaps[r]) if overlaps else None
        self.status: str = row["status"]

    @property
    def scorable(self) -> bool:
        return bool(self.audible)

    @property
    def top1_main(self) -> bool:
        """Strict: the reported ayah is the one heard for the longest time."""
        return self.status in ("match", "ambiguous") and self.row["best"] == self.main

    @property
    def top1(self) -> bool:
        """The reported ayah is one that is actually heard in the clip."""
        return self.status in ("match", "ambiguous") and self.row["best"] in self.audible

    @property
    def top3(self) -> bool:
        return self.status in ("match", "ambiguous") and bool(
            self.audible & set(self.row["ranked"])
        )

    @property
    def truth_offered(self) -> bool:
        if self.status == "match":
            return self.row["best"] in self.audible
        return self.status == "ambiguous" and bool(self.audible & set(self.row["alternatives"]))

    @property
    def wrong_match(self) -> bool:
        return self.status == "match" and self.row["best"] not in self.audible


def accuracy_row(label: list[str], items: list[Scored]) -> list[str]:
    n = len(items)
    return [
        *label,
        str(n),
        pct(sum(s.top1 for s in items), n),
        pct(sum(s.top1_main for s in items), n),
        pct(sum(s.top3 for s in items), n),
        pct(sum(s.truth_offered for s in items), n),
        pct(sum(s.wrong_match for s in items), n),
        pct(sum(s.status == "ambiguous" for s in items), n),
        pct(sum(s.status == "no_match" for s in items), n),
    ]


ACCURACY_HEADER = [
    "Clips",
    "Top-1",
    "Top-1 (longest ayah)",
    "Top-3",
    "Truth offered",
    "Wrong match",
    "ambiguous",
    "no_match",
]


def load_scored(name: str, clips: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[Scored]]:
    payload = json.loads((RESULTS_DIR / f"{name}.json").read_text())
    return payload, [Scored(clips[row["clip_id"]], row) for row in payload["results"]]


def report() -> None:
    clips = {c["clip_id"]: c for c in load_manifest()}
    meta, scored = load_scored(PRIMARY_MODEL, clips)
    positives = [s for s in scored if s.clip["condition"] != "negative"]
    negatives = [s for s in scored if s.clip["condition"] == "negative"]
    usable = [s for s in positives if s.scorable]
    random_clips = [s for s in usable if s.clip["kind"] == "random"]

    def pick(items: list[Scored], **where: Any) -> list[Scored]:
        return [s for s in items if all(s.clip[k] == v for k, v in where.items())]

    # ---- targets ----
    clean8 = pick(random_clips, condition="clean", duration=8.0)
    top1_clean8 = sum(s.top1 for s in clean8) / len(clean8)
    clean8_rest = [s for s in clean8 if s.clip["reciter"] != WORST]
    top1_clean8_rest = sum(s.top1 for s in clean8_rest) / len(clean8_rest)
    totals = [s.row["timings_ms"]["total"] for s in positives if "timings_ms" in s.row]
    p95_total = percentile(totals, 0.95)

    def verdict(ok: bool) -> str:
        return "met" if ok else "NOT met"

    # ---- accuracy by condition x duration ----
    grid_rows = [
        accuracy_row(
            [condition, f"{duration:g} s"],
            pick(random_clips, condition=condition, duration=duration),
        )
        for condition in ("clean", "phone")
        for duration in (5.0, 8.0, 12.0)
    ]
    style_rows = [
        accuracy_row([style, condition], pick(random_clips, style=style, condition=condition))
        for style in ("murattal", "mujawwad")
        for condition in ("clean", "phone")
    ]
    prefix_rows = []
    for condition in ("clean", "phone"):
        items = [
            s for s in usable if s.clip["kind"] == "prefix" and s.clip["condition"] == condition
        ]
        detected = sum(bool(s.row.get("prefix_detected")) for s in items if s.clip["prefix"])
        with_prefix = sum(bool(s.clip["prefix"]) for s in items)
        prefix_rows.append([*accuracy_row([condition], items), pct(detected, with_prefix)])

    # ---- per reciter (clean + phone, random clips) ----
    by_reciter: defaultdict[str, list[Scored]] = defaultdict(list)
    for s in random_clips:
        by_reciter[s.clip["reciter"]].append(s)
    reciter_rows = sorted(
        (
            [
                reciter,
                items[0].clip["style"],
                str(len(items)),
                pct(sum(s.top1 for s in pick(items, condition="clean")), len(items) // 2),
                pct(sum(s.top1 for s in pick(items, condition="phone")), len(items) // 2),
            ]
            for reciter, items in by_reciter.items()
        ),
        key=lambda row: float(row[3].rstrip("%")) + float(row[4].rstrip("%")),
    )

    # ---- failures ----
    failures = [s for s in random_clips if not s.truth_offered]
    failure_reasons = Counter(
        (
            s.status
            + (f" ({s.row['reason']})" if s.row.get("reason") else "")
            + (" [" + ",".join(s.row["guard_flags"]) + "]" if s.row.get("guard_flags") else "")
        )
        for s in failures
    )
    failure_rows = [[k, str(v), pct(v, len(failures))] for k, v in failure_reasons.most_common()]

    # ---- negatives ----
    negative_rows = []
    for kind in ("silence", "noise", "tones"):
        items = [s for s in negatives if s.clip["kind"] == kind]
        reasons = Counter(
            f"{s.status}" + (f" ({s.row['reason']})" if s.row.get("reason") else "") for s in items
        )
        negative_rows.append(
            [
                kind,
                str(len(items)),
                pct(sum(s.status == "no_match" for s in items), len(items)),
                ", ".join(f"{k}: {v}" for k, v in reasons.most_common()),
            ]
        )

    # ---- latency ----
    latency_rows = []
    for stage in ("decode", "vad", "asr", "match", "total"):
        for condition in ("clean", "phone"):
            values = [
                s.row["timings_ms"][stage]
                for s in positives
                if s.clip["condition"] == condition and stage in s.row.get("timings_ms", {})
            ]
            latency_rows.append(
                [
                    stage,
                    condition,
                    str(len(values)),
                    f"{percentile(values, 0.50):.0f}",
                    f"{percentile(values, 0.95):.0f}",
                    f"{max(values):.0f}",
                ]
            )
    by_duration_rows = [
        [
            f"{duration:g} s",
            f"{percentile([s.row['timings_ms']['total'] for s in pick(positives, duration=duration)], 0.50):.0f}",
            f"{percentile([s.row['timings_ms']['total'] for s in pick(positives, duration=duration)], 0.95):.0f}",
        ]
        for duration in (5.0, 8.0, 12.0)
    ]

    # ---- VAD ----
    ratios = [s.row["speech_sec"] / s.clip["duration"] for s in positives if "speech_sec" in s.row]
    vad_rejects = sum(
        s.row.get("reason") == "no_speech" and not s.row.get("guard_flags") for s in positives
    )

    # ---- confidence signals ----
    def scores(ok: bool) -> list[float]:
        return [s.row["score"] for s in random_clips if s.row.get("score") and s.top1 == ok]

    good, bad = scores(True), scores(False)
    threshold_rows = []
    all_scores = [(s.row["score"], s.top1) for s in random_clips if s.row.get("score")]
    for threshold in (76, 80, 85, 90, 95):
        accepted = [ok for score, ok in all_scores if score >= threshold]
        threshold_rows.append(
            [
                ("**" + str(threshold) + "**")
                if threshold == meta["match_threshold"]
                else str(threshold),
                pct(len(accepted), len(random_clips)),
                pct(sum(accepted), len(accepted)),
                pct(len(accepted) - sum(accepted), len(random_clips)),
            ]
        )

    # ---- model comparison on the shared subset ----
    comparison_rows, model_notes = [], []
    for name in (PRIMARY_MODEL, *COMPARISON_MODELS):
        if not (RESULTS_DIR / f"{name}.json").is_file():
            continue
        payload, items = load_scored(name, clips)
        subset = [
            s
            for s in items
            if s.scorable and s.clip["kind"] == "random" and in_comparison_subset(s.clip)
        ]
        times = [
            s.row["timings_ms"]
            for s in items
            if in_comparison_subset(s.clip)
            and s.clip["condition"] != "negative"
            and "timings_ms" in s.row
        ]
        size_mb = sum(f.stat().st_size for f in (MODELS_DIR / name).iterdir()) / 1e6
        clean = pick(subset, condition="clean")
        phone = pick(subset, condition="phone")
        comparison_rows.append(
            [
                f"`{name}`",
                f"{size_mb:.0f} MB",
                pct(sum(s.top1 for s in clean), len(clean)),
                pct(sum(s.top1 for s in phone), len(phone)),
                pct(sum(s.wrong_match for s in clean + phone), len(clean + phone)),
                f"{percentile([t['asr'] for t in times if 'asr' in t], 0.50):.0f}",
                f"{percentile([t['asr'] for t in times if 'asr' in t], 0.95):.0f}",
                f"{percentile([t['total'] for t in times], 0.95):.0f}",
            ]
        )
        src = payload["source"]
        model_notes.append(
            f"- `{name}`: `{src['repo']}` @ `{src['commit'][:10]}`, {src['license']}, "
            f"CTranslate2 {src['quantization']}"
        )

    n_reciters = len({s.clip["reciter"] for s in positives})
    unscorable = len(positives) - len(usable)
    text = f"""# Phase 2 — end-to-end ayah identification on real audio

Generated by `ml/eval/audio_eval.py report` from stored runs. Every number below
comes from those runs; nothing is estimated.

- Machine: {meta["machine"]}, Python {meta["python"]}
- Pipeline: PyAV decode → Silero VAD gate (threshold {meta["vad_threshold"]:g}, trimming {"on" if meta["vad_trim_silence"] else "off"}) → faster-whisper (int8, {meta["cpu_threads"]} CPU threads,
  beam {meta["beam_size"]}) → hallucination guards → ayah matcher
  (`MATCH_THRESHOLD` {meta["match_threshold"]:g}, `AMBIGUITY_DELTA` {meta["ambiguity_delta"]:g})
- Model used for all tables unless stated: `{PRIMARY_MODEL}`
- One request at a time (no concurrency)

## Targets

| Target | Result | Verdict |
| --- | --- | --- |
| Top-1 ≥ 90% on clean 8 s clips | {100 * top1_clean8:.1f}% ({len(clean8)} clips) | {verdict(top1_clean8 >= TARGET_TOP1)} |
| End-to-end p95 < 2.5 s on 4 vCPU | {p95_total / 1000:.2f} s ({len(totals)} clips) | {verdict(p95_total < TARGET_P95_MS)} |

## Read this first: what these numbers can and cannot tell you

**The ASR models were trained on EveryAyah, the same recordings this evaluation
uses.** The published dataset's train, validation and test splits contain the
same reciters, so these reciters, and very likely these exact ayahs, were seen
in training. The results therefore show how the system does on *studio
recordings of well-known reciters*. They are an upper bound for anything else:
an unknown reciter, a live mosque recording, or a phone held near a speaker.
The "phone" condition is simulated, not recorded.

## Evaluation set

{len(positives)} clips from {n_reciters} reciters (26 murattal, 2 mujawwad), cut from
{len(HELDOUT)} held-out surahs ({", ".join(str(s) for s in HELDOUT)}). Consecutive ayahs are concatenated and
windows are cut at random offsets, so clips start and end mid-ayah and usually
cross ayah boundaries.

- **clean**: the original recording, 16 kHz WAV.
- **phone**: synthetic room reverb (RT60 0.25–0.6 s), pink noise at 10–20 dB SNR,
  250–3600 Hz band-limit, then Opus at 16–24 kbps in WebM.
- **prefix** clips start at the beginning of a surah with a basmala (and an
  isti'adha where the reciter's folder has one) in front.
- Plus {len(negatives)} non-speech clips (silence, noise, tones).

Ground truth is time-based: for each clip we know how many seconds of each ayah
are heard. An ayah is "in the clip" if at least {AUDIBLE_SEC:g} s of it is heard.
{unscorable} prefix clips contain less than that of any ayah (the prefix fills them)
and are left out of the accuracy tables.

Column meanings:

- **Top-1**: the reported ayah is in the clip.
- **Top-1 (longest ayah)**: stricter — it is the ayah heard for the longest time.
- **Top-3**: an ayah in the clip is among the three best candidates.
- **Truth offered**: a correct match, or an ambiguous result listing a correct location.
- **Wrong match**: status `match` naming an ayah that is not in the clip (the harmful case).

## One reciter fails completely

`{WORST}` scores 0% in both conditions, with all three models, and its
ayahs are mis-transcribed even when played whole. Its recordings are also much
quieter than the others. Whether the cause is the source audio or that the
models never saw this reciter is not established. It is kept in every table.
Without that one folder, Top-1 on clean 8 s clips is
{100 * top1_clean8_rest:.1f}% ({len(clean8_rest)} clips) — reported for context, not as the result.

## Accuracy by condition and clip length (random clips)

{table(["Condition", "Length", *ACCURACY_HEADER], grid_rows)}

## Accuracy by recitation style (random clips, all lengths)

{table(["Style", "Condition", *ACCURACY_HEADER], style_rows)}

## Clips that start with isti'adha / basmala

{table(["Condition", *ACCURACY_HEADER, "Prefix detected"], prefix_rows)}

## Where it fails (random clips where the truth was not offered: {len(failures)} of {len(random_clips)})

{table(["Outcome", "Clips", "Share of failures"], failure_rows)}

## Per reciter, worst first (random clips, Top-1)

{table(["Reciter folder", "Style", "Clips", "Clean", "Phone"], reciter_rows)}

## Non-speech clips

All of these must come back as `no_match`.

{table(["Kind", "Clips", "Rejected", "Outcomes"], negative_rows)}

There are **no non-Quran speech negatives** in this evaluation (ordinary Arabic
speech, songs, a sermon). That is the realistic false-accept risk and it is
untested.

## Latency per stage (ms)

{table(["Stage", "Condition", "Clips", "p50", "p95", "max"], latency_rows)}

Total by clip length:

{table(["Length", "p50", "p95"], by_duration_rows)}

## Voice activity detection

Detected speech covers a median of {100 * percentile(ratios, 0.5):.0f}% of each clip
(5th percentile {100 * percentile(ratios, 0.05):.0f}%). {vad_rejects} of {len(positives)} recitation clips were
rejected by the VAD gate for having under 1.5 s of detected speech.

The detector is run far more permissively than usual (threshold {meta["vad_threshold"]:g}
instead of 0.5) and is used only as a gate, without trimming. With the usual
settings it rejected 6.7% of clean and 32.6% of phone-like recitation clips. The
experiments behind that choice are in `docs/plans/phase-2.md`; note that the
setting was chosen on a sample of this same evaluation set.

## Match score as a confidence signal (random clips)

Median score when Top-1 is right: {percentile(good, 0.5):.1f} ({len(good)} clips); when wrong:
{percentile(bad, 0.5) if bad else float("nan"):.1f} ({len(bad)} clips). "Wrong" here includes
ambiguous results whose first-listed location is not the right one.

Raising the threshold above the current value (results below it are already
`no_match`, so lower values cannot be read from this run):

{table(["`MATCH_THRESHOLD`", "Clips accepted", "Top-1 among accepted", "Not Top-1 but accepted (of all clips)"], threshold_rows)}

The score does not separate right from wrong well: a short transcript can
match the wrong place perfectly. Raising the threshold costs many correct
answers for little gain, so it stays at {meta["match_threshold"]:g}.

## Model comparison (8 s random clips only)

{table(["Model", "Size", "Top-1 clean", "Top-1 phone", "Wrong match", "ASR p50 ms", "ASR p95 ms", "Total p95 ms"], comparison_rows)}

{chr(10).join(model_notes)}
"""
    REPORT.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {REPORT.relative_to(REPO)}")


sys.path.insert(0, str(REPO / "ml" / "eval"))
from heldout import HELDOUT_SURAHS as HELDOUT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--models", nargs="*", default=[PRIMARY_MODEL, *COMPARISON_MODELS])
    sub.add_parser("report")
    args = parser.parse_args()

    if args.command == "report":
        report()
        return 0

    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    clips = load_manifest()
    for name in args.models:
        subset = clips if name == PRIMARY_MODEL else [c for c in clips if in_comparison_subset(c)]
        run_model(name, subset, settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
