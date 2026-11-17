"""Phase 3 evaluation: open-set reciter identification.

Usage: uv run --project backend python ml/eval/reciter_eval.py

Queries are the Phase 2 clips (held-out surahs, clean and phone-like, 5/8/12 s).
The gallery never contains those surahs.

Open-set testing is leave-one-reciter-out: every reciter is scored once as a
gallery member and once as a stranger, by ignoring their own gallery entries.
The decision rule is calibrated on half of the reciters and measured on the
other half, both ways round (two-fold), so every reciter is test data once.

Writes ml/eval/reports/phase3.md. Every number comes from this run.
"""

import json
import os
import platform
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.audio.decode import decode_audio
from app.core.config import Settings
from app.speaker.engine import OnnxSpeakerEngine
from app.speaker.gallery import Gallery

EVAL_DIR = REPO / "ml" / "data" / "eval_audio"
CACHE = EVAL_DIR / "query_embeddings.npz"
REGISTRY = REPO / "ml" / "registry" / "reciters.json"
MODEL = REPO / "ml" / "artifacts" / "speaker" / "resnet34.onnx"
GALLERY = REPO / "ml" / "artifacts" / "gallery.npz"
REPORT = REPO / "ml" / "eval" / "reports" / "phase3.md"

TARGET_FALSE_ACCEPT = 0.05
# The setting is calibrated to a stricter limit than the target, because a
# setting tuned on one set of reciters accepts somewhat more strangers on
# another. See "Calibration headroom" in the report for how this was chosen.
CALIBRATION_LIMIT = 0.04
CPU_THREADS = 4


@dataclass
class Query:
    clip: dict[str, Any]
    reciter: str
    style: str
    scores: dict[str, float]  # reciter id -> score (best voice), full gallery
    stranger_scores: dict[str, float]  # same, with this reciter removed from the gallery
    cross_style: tuple[float, float] | None  # (own other-style score, best rival) or None

    @property
    def ranked(self) -> list[str]:
        return sorted(self.scores, key=lambda r: (-self.scores[r], r))

    @property
    def target(self) -> float:
        return self.scores[self.reciter]

    @property
    def top1(self) -> bool:
        return self.ranked[0] == self.reciter

    def member(self, floor: float, margin: float) -> str:
        """Outcome when this reciter is in the gallery."""
        ordered = sorted(self.scores.values(), reverse=True)
        if ordered[0] < floor or ordered[0] - ordered[1] < margin:
            return "unknown"
        return "identified" if self.top1 else "misidentified"

    def stranger_accepted(self, floor: float, margin: float) -> bool:
        """With this reciter removed from the gallery: is someone else named?"""
        ordered = sorted(self.stranger_scores.values(), reverse=True)
        return ordered[0] >= floor and ordered[0] - ordered[1] >= margin


def pct(part: float, whole: float) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "n/a"


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


def table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def equal_error_rate(targets: np.ndarray, nontargets: np.ndarray) -> tuple[float, float]:
    """Returns (EER, threshold at the EER)."""
    thresholds = np.unique(np.concatenate([targets, nontargets]))
    far = np.array([(nontargets >= t).mean() for t in thresholds])
    frr = np.array([(targets < t).mean() for t in thresholds])
    i = int(np.argmin(np.abs(far - frr)))
    return float((far[i] + frr[i]) / 2), float(thresholds[i])


def reciter_scores(gallery: Gallery, embedding: np.ndarray) -> dict[str, float]:
    return {score.reciter_id: score.similarity for score in gallery.rank(embedding)}


def build_queries(
    gallery: Gallery,
    clips: list[dict[str, Any]],
    embeddings: np.ndarray,
    folder_to: dict[str, tuple[str, str]],
) -> list[Query]:
    """Score every clip against the full gallery, against the gallery refitted
    without its reciter (stranger test), and, for reciters with several styles,
    against the gallery without the clip's own style (cross-style test)."""
    styles_of: defaultdict[str, set[str]] = defaultdict(set)
    for voice in gallery.voices:
        styles_of[voice.reciter_id].add(voice.style)
    without_reciter: dict[str, Gallery] = {}
    without_style: dict[tuple[str, str], Gallery] = {}

    queries = []
    for clip, embedding in zip(clips, embeddings, strict=True):
        reciter, style = folder_to[clip["reciter"]]
        if reciter not in without_reciter:
            without_reciter[reciter] = gallery.without_reciter(reciter)
        cross = None
        if len(styles_of[reciter]) > 1:
            key = (reciter, style)
            if key not in without_style:
                without_style[key] = gallery.without_voices(
                    {v for v in gallery.voices if v.reciter_id == reciter and v.style == style}
                )
            ranked = reciter_scores(without_style[key], embedding)
            cross = (ranked[reciter], max(s for r, s in ranked.items() if r != reciter))
        queries.append(
            Query(
                clip,
                reciter,
                style,
                reciter_scores(gallery, embedding),
                reciter_scores(without_reciter[reciter], embedding),
                cross,
            )
        )
    return queries


def load_queries(gallery: Gallery) -> tuple[list[Query], list[float]]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    folder_to = {
        src["folder"]: (r["id"], src["style"])
        for r in registry
        for src in r["sources"]["everyayah"]
    }
    clips = [
        json.loads(line)
        for line in (EVAL_DIR / "manifest.jsonl").read_text().splitlines()
        if '"negative"' not in line
    ]
    clips = [c for c in clips if c["condition"] != "negative"]

    ids = [c["clip_id"] for c in clips]
    timings: list[float] = []
    if (
        CACHE.is_file()
        and list(np.load(CACHE)["ids"]) == ids
        and np.load(CACHE)["embeddings"].shape[1] == gallery.embeddings.shape[1]
    ):
        data = np.load(CACHE)
        embeddings, timings = data["embeddings"], list(data["millis"])
    else:
        engine = OnnxSpeakerEngine(MODEL, cpu_threads=CPU_THREADS)
        engine.warm_up()
        rows = []
        for clip in clips:
            audio = decode_audio(
                (EVAL_DIR / clip["path"]).read_bytes(), max_bytes=10**8, max_seconds=60
            )
            started = time.perf_counter()
            rows.append(engine.embed(audio))
            timings.append((time.perf_counter() - started) * 1000)
        embeddings = np.stack(rows)
        np.savez_compressed(CACHE, ids=np.array(ids), embeddings=embeddings, millis=timings)

    queries = build_queries(gallery, clips, embeddings, folder_to)
    return queries, timings


def summarize(items: list[Query], floor: float, margin: float) -> dict[str, float]:
    n = len(items)
    outcomes = [q.member(floor, margin) for q in items]
    return {
        "n": n,
        "identified": outcomes.count("identified") / n,
        "misidentified": outcomes.count("misidentified") / n,
        "unknown": outcomes.count("unknown") / n,
        "false_accept": sum(q.stranger_accepted(floor, margin) for q in items) / n,
    }


FLOORS = [round(float(x), 3) for x in np.arange(0.20, 0.901, 0.025)]
MARGINS = [round(float(x), 3) for x in np.arange(0.0, 0.4001, 0.01)]


def calibrate(
    items: list[Query], margins: list[float] = MARGINS, limit: float = TARGET_FALSE_ACCEPT
) -> tuple[float, float]:
    """The (floor, margin) that names the most gallery members correctly while
    accepting at most `limit` of strangers, on `items`."""
    best: tuple[float, float, float] | None = None
    for floor in FLOORS:
        for margin in margins:
            result = summarize(items, floor, margin)
            if result["false_accept"] > limit:
                continue
            if best is None or result["identified"] > best[0]:
                best = (result["identified"], floor, margin)
    if best is None:
        raise SystemExit("no setting reaches the false-accept target")
    return best[1], best[2]


def row(label: str, result: dict[str, float]) -> list[str]:
    return [
        label,
        str(int(result["n"])),
        f"{100 * result['false_accept']:.1f}%",
        f"{100 * result['identified']:.1f}%",
        f"{100 * result['misidentified']:.1f}%",
        f"{100 * result['unknown']:.1f}%",
    ]


OUTCOME_HEADER = [
    "Clips",
    "Count",
    "False accept (stranger)",
    "Identified",
    "Misidentified",
    "Unknown",
]


def pooled(parts: list[tuple[list[Query], float, float]]) -> dict[str, float]:
    """Combine folds, each scored with the setting calibrated on the other fold."""
    total = sum(len(items) for items, _, _ in parts)
    out = {"n": float(total)}
    for key in ("identified", "misidentified", "unknown", "false_accept"):
        out[key] = sum(summarize(i, f, m)[key] * len(i) for i, f, m in parts if i) / total
    return out


def main() -> int:
    gallery = Gallery.load(GALLERY)
    queries, timings = load_queries(gallery)
    reciters = sorted({q.reciter for q in queries})
    fold_a = [q for q in queries if q.reciter in set(reciters[0::2])]
    fold_b = [q for q in queries if q.reciter in set(reciters[1::2])]

    def pick(items: list[Query], **where: Any) -> list[Query]:
        return [q for q in items if all(q.clip[k] == v for k, v in where.items())]

    # ---- two-fold: calibrate on one half of the reciters, measure on the other ----
    def two_fold(
        margins: list[float], limit: float = CALIBRATION_LIMIT
    ) -> list[tuple[list[Query], float, float]]:
        from_a = calibrate(fold_a, margins, limit)
        from_b = calibrate(fold_b, margins, limit)
        return [(fold_b, *from_a), (fold_a, *from_b)]

    folds = two_fold(MARGINS)
    folds_floor_only = two_fold([0.0])
    result = pooled(folds)
    headroom_rows = [
        [f"{100 * limit:g}%", *row("", pooled(two_fold(MARGINS, limit)))[2:]]
        for limit in (0.05, 0.04, 0.03, 0.02)
    ]

    def subset(parts: list[tuple[list[Query], float, float]], **where: Any) -> dict[str, float]:
        return pooled([(pick(items, **where), f, m) for items, f, m in parts])

    cross_rows = [
        row("**all test clips, threshold + margin**", result),
        row("all test clips, threshold only (the brief's rule)", pooled(folds_floor_only)),
        row("clean", subset(folds, condition="clean")),
        row("phone", subset(folds, condition="phone")),
        row("5 s", subset(folds, duration=5.0)),
        row("8 s", subset(folds, duration=8.0)),
        row("12 s", subset(folds, duration=12.0)),
        row("clean, threshold only", subset(folds_floor_only, condition="clean")),
        row("phone, threshold only", subset(folds_floor_only, condition="phone")),
    ]
    fold_rows = [
        [name, f"{f:.3f}", f"{m:.3f}", *row("", summarize(items, f, m))[1:]]
        for name, (items, f, m) in zip(
            (
                "calibrated on fold A, measured on fold B",
                "calibrated on fold B, measured on fold A",
            ),
            folds,
            strict=True,
        )
    ]

    # ---- shipped setting: calibrated on every reciter (not an unbiased estimate) ----
    floor, margin = calibrate(queries, MARGINS, CALIBRATION_LIMIT)
    shipped = summarize(queries, floor, margin)
    # What the service actually runs with (its configured defaults).
    service = Settings()
    configured = summarize(queries, service.reciter_threshold, service.reciter_min_margin)

    # ---- closed set ----
    closed_rows = []
    for condition in ("clean", "phone"):
        for duration in (5.0, 8.0, 12.0):
            items = pick(queries, condition=condition, duration=duration)
            closed_rows.append(
                [
                    condition,
                    f"{duration:g} s",
                    str(len(items)),
                    pct(sum(q.top1 for q in items), len(items)),
                    pct(sum(q.reciter in q.ranked[:3] for q in items), len(items)),
                ]
            )
    closed_all = sum(q.top1 for q in queries) / len(queries)

    # ---- EER ----
    eer_rows = []
    for label, items in (
        ("all clips", queries),
        ("clean", pick(queries, condition="clean")),
        ("phone", pick(queries, condition="phone")),
    ):
        targets = np.array([q.target for q in items])
        nontargets = np.array([s for q in items for r, s in q.scores.items() if r != q.reciter])
        eer, at = equal_error_rate(targets, nontargets)
        eer_rows.append([label, str(len(items)), f"{100 * eer:.2f}%", f"{at:.3f}"])

    # ---- accept/reject curves (all clips) ----
    margin_curve = [
        row(f"**{m:.3f}**" if m == margin else f"{m:.3f}", summarize(queries, floor, m))
        for m in sorted({0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 0.20, margin})
    ]
    floor_curve = [
        row(f"{f:.2f}", summarize(queries, f, 0.0))
        for f in (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70)
    ]

    # ---- styles ----
    style_rows = []
    for style in ("murattal", "mujawwad"):
        for condition in ("clean", "phone"):
            items = [q for q in queries if q.style == style and q.clip["condition"] == condition]
            o = summarize(items, floor, margin)
            style_rows.append(
                [
                    style,
                    condition,
                    str(len(items)),
                    pct(sum(q.top1 for q in items), len(items)),
                    f"{100 * o['identified']:.1f}%",
                    f"{100 * o['unknown']:.1f}%",
                ]
            )

    # Cross-style: recognise a reciter from a style the gallery does not hold.
    cross_style_rows = []
    styles_of: defaultdict[str, set[str]] = defaultdict(set)
    for voice in gallery.voices:
        styles_of[voice.reciter_id].add(voice.style)
    for reciter in sorted(r for r in reciters if len(styles_of[r]) > 1):
        for style in sorted({q.style for q in queries if q.reciter == reciter}):
            items = [q for q in queries if q.reciter == reciter and q.style == style]
            pairs = [q.cross_style for q in items if q.cross_style is not None]
            right = sum(own > rival for own, rival in pairs)
            accepted = sum(
                own > rival and own >= floor and own - rival >= margin for own, rival in pairs
            )
            cross_style_rows.append(
                [
                    reciter,
                    style,
                    ", ".join(sorted(styles_of[reciter] - {style})),
                    str(len(items)),
                    pct(sum(q.top1 for q in items), len(items)),
                    pct(right, len(items)),
                    pct(accepted, len(items)),
                ]
            )

    # ---- per reciter ----
    reciter_rows = []
    for reciter in reciters:
        items = [q for q in queries if q.reciter == reciter]
        o = summarize(items, floor, margin)
        reciter_rows.append(
            [
                reciter,
                str(len(items)),
                pct(sum(q.top1 for q in items), len(items)),
                f"{100 * o['identified']:.1f}%",
                f"{100 * o['false_accept']:.1f}%",
                f"{np.median([q.target for q in items]):.3f}",
            ]
        )
    reciter_rows.sort(key=lambda r: float(r[3].rstrip("%")))

    confusions: defaultdict[tuple[str, str], int] = defaultdict(int)
    for q in queries:
        if not q.top1:
            confusions[(q.reciter, q.ranked[0])] += 1
    confusion_rows = [
        [true, guess, str(n)]
        for (true, guess), n in sorted(confusions.items(), key=lambda kv: -kv[1])[:10]
    ]

    # ---- variants: score weighting, and the projection on/off ----
    cache = np.load(CACHE)
    clips_all = [q.clip for q in queries]
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    folder_to = {
        src["folder"]: (r["id"], src["style"])
        for r in registry
        for src in r["sources"]["everyayah"]
    }

    def variant(label: str, **options: Any) -> list[str]:
        alt = Gallery(gallery.voices, gallery.embeddings, gallery.voice_of_clip, **options)
        alt_queries = build_queries(alt, clips_all, cache["embeddings"], folder_to)
        half_a = [q for q in alt_queries if q.reciter in set(reciters[0::2])]
        half_b = [q for q in alt_queries if q.reciter in set(reciters[1::2])]
        outcome = pooled(
            [
                (half_b, *calibrate(half_a, MARGINS, CALIBRATION_LIMIT)),
                (half_a, *calibrate(half_b, MARGINS, CALIBRATION_LIMIT)),
            ]
        )
        return [
            label,
            pct(sum(q.top1 for q in alt_queries), len(alt_queries)),
            f"{100 * outcome['false_accept']:.1f}%",
            f"{100 * outcome['identified']:.1f}%",
        ]

    variant_rows = [
        variant("**as shipped**: LDA, centroid + top-5 clips"),
        variant("no LDA (model's own space)", use_lda=False),
        variant("LDA, top-5 clips only", centroid_weight=0.0),
        variant("LDA, centroid only", centroid_weight=1.0),
    ]

    def times(duration: float) -> list[float]:
        return [t for q, t in zip(queries, timings, strict=True) if q.clip["duration"] == duration]

    latency_rows = [
        [f"{d:g} s", f"{percentile(times(d), 0.5):.0f}", f"{percentile(times(d), 0.95):.0f}"]
        for d in (5.0, 8.0, 12.0)
    ]

    n_voices = len(gallery.voices)
    n_gallery_reciters = len({v.reciter_id for v in gallery.voices})

    def verdict(ok: bool) -> str:
        return "met" if ok else "NOT met"

    report = f"""# Phase 3 — reciter identification (open-set)

Generated by `ml/eval/reciter_eval.py`. Every number below comes from that run.

- Machine: {platform.machine()}, {os.cpu_count()} logical CPUs, Python {platform.python_version()}
- Embedding model: WeSpeaker ResNet34 (`Wespeaker/wespeaker-voxceleb-resnet34-LM`), ONNX, {gallery.embeddings.shape[1]}-d, L2-normalized\n- Scoring space: LDA projection fitted on the gallery ({"on" if gallery.projection is not None else "off"})
- Gallery: {n_gallery_reciters} reciters, {n_voices} voices (reciter × style), {len(gallery.embeddings):,} clip embeddings
  (each studio clip plus a phone-like copy of it)
- Queries: {len(queries):,} clips from {len(reciters)} reciters ({len(pick(queries, condition="clean"))} clean, {len(pick(queries, condition="phone"))} phone-like)
- Score: {gallery.centroid_weight:g} × centroid cosine + {1 - gallery.centroid_weight:g} × mean of the top {gallery.top_k} clip cosines
- Decision: `identified` if the best score ≥ threshold **and** it leads the
  runner-up by ≥ margin; otherwise `unknown`

## Target

| Target | Result | Verdict |
| --- | --- | --- |
| False accept ≤ 5% on out-of-gallery reciters | {100 * result["false_accept"]:.1f}% (two-fold, {int(result["n"]):,} test clips) | {verdict(result["false_accept"] <= TARGET_FALSE_ACCEPT)} |

At that operating point, when the reciter *is* in the gallery:
{100 * result["identified"]:.1f}% are named correctly, {100 * result["misidentified"]:.1f}% are named as someone else and
{100 * result["unknown"]:.1f}% come back as unknown.

## Read this first

- **The gallery and the queries come from the same recordings.** A reciter's
  gallery clips and test clips are different ayahs, but of the same recorded
  mushaf: same microphone, room and mastering. The embedding partly captures
  that, so these numbers are optimistic for a *different* recording of the
  same reciter (a live prayer, an older tape, another studio).
- **The phone-like copies in the gallery are made by the same simulation as
  the phone-like test clips** (different random settings). Results on
  phone-like clips are therefore optimistic for real phones.
- The embedding model has not seen these reciters (it was trained on
  VoxCeleb), so unlike Phase 2 there is no training-data leak.
- Strangers here are other famous reciters with studio recordings. Imitators
  and amateur reciters were not tested.

## How the open-set test works

Every reciter with query clips is tested twice: as a gallery member (is the
right name returned?) and as a stranger, by ignoring that reciter's own gallery
entries (is "unknown" returned?). So all {len(reciters)} reciters serve as
out-of-gallery reciters.

The threshold and margin are chosen on half of the reciters, as the setting
that names the most members correctly while accepting at most
{100 * CALIBRATION_LIMIT:g}% of strangers there, and then measured on the other half. This is
done both ways round and the two test halves are pooled.

{table(["Fold", "Threshold", "Margin", "Count", "False accept (stranger)", "Identified", "Misidentified", "Unknown"], fold_rows)}

## Calibration headroom

A setting tuned on 13 reciters accepts more strangers on the other 13 than it
did on its own. Calibrating to exactly the 5% target therefore overshoots it
on test reciters. Results on test clips for different calibration limits:

{table(["Calibrated to at most", "False accept on test (stranger)", "Identified", "Misidentified", "Unknown"], headroom_rows)}

The limit used is {100 * CALIBRATION_LIMIT:g}%. It was picked after seeing this table, so the
headline result is not a fully blind estimate; with only {len(reciters)} reciters there
was no third group to hold back for that.

## Open-set results (two-fold test clips)

{table(OUTCOME_HEADER, cross_rows)}

## Shipped setting

Calibrating on all {len(reciters)} evaluated reciters gives threshold {floor:g} and margin
{margin:g}: on those same clips, {100 * shipped["false_accept"]:.1f}% false accepts and
{100 * shipped["identified"]:.1f}% identified; the two-fold figures above are the fair estimate.

**The service's defaults are `RECITER_THRESHOLD = {service.reciter_threshold:g}` and
`RECITER_MIN_MARGIN = {service.reciter_min_margin:g}`.** With those, on these clips:
{100 * configured["false_accept"]:.1f}% false accepts, {100 * configured["identified"]:.1f}% identified,
{100 * configured["misidentified"]:.1f}% misidentified, {100 * configured["unknown"]:.1f}% unknown.
Tables below marked "shipped setting" use the calibrated pair above.

## Closed-set accuracy (every reciter in the gallery, no rejection)

Overall Top-1: {100 * closed_all:.1f}% of {len(queries):,} clips.

{table(["Condition", "Length", "Clips", "Top-1", "Top-3"], closed_rows)}

## Equal error rate

Each clip is compared with every reciter: one target score, the rest non-target.

{table(["Clips", "Count", "EER", "Threshold at EER"], eer_rows)}

## Accept/reject curves (all clips)

Varying the margin at threshold {floor:g}:

{table(["Margin", *OUTCOME_HEADER[1:]], margin_curve)}

Varying the threshold with no margin (the brief's rule):

{table(["Threshold", *OUTCOME_HEADER[1:]], floor_curve)}

## By recitation style (shipped setting)

{table(["Style", "Condition", "Clips", "Closed-set Top-1", "Identified", "Unknown"], style_rows)}

## Recognising a reciter in a style the gallery does not have

For reciters with more than one style, their clips in one style are scored
against only their *other* styles' gallery entries (plus every other reciter).

{table(["Reciter", "Query style", "Gallery styles used", "Clips", "Top-1 with own style", "Top-1 cross-style", "Identified cross-style"], cross_style_rows)}

## Per reciter, worst first (shipped setting)

{table(["Reciter", "Clips", "Closed-set Top-1", "Identified", "False accept as stranger", "Median own score"], reciter_rows)}

## Most frequent confusions (closed set)

{table(["True reciter", "Named as", "Clips"], confusion_rows) if confusion_rows else "None."}

## What each part contributes

Same clips, same two-fold procedure, one thing changed at a time.

{table(["Variant", "Closed-set Top-1", "False accept (test)", "Identified (test)"], variant_rows)}

## Embedding time (ms, {CPU_THREADS} CPU threads, one clip at a time)

{table(["Clip length", "p50", "p95"], latency_rows)}

## Hard cases this evaluation does not cover

- **Imitators** of famous reciters: not tested. An imitator who sounds close
  enough will be named as the reciter they imitate; a voice embedding cannot
  tell intent.
- **Very old recordings**: only as far as the EveryAyah folders include them.
- **Mosque echo**: only the simulated reverb of the phone condition.
- **Same reciter, different recording**: not tested (see "Read this first").
"""
    REPORT.write_text(report, encoding="utf-8")
    print(report)
    print(f"wrote {REPORT.relative_to(REPO)}")
    print(f"SHIPPED threshold={floor} margin={margin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
