"""Phase 1 text-only evaluation of the ayah matcher (no audio).

Samples random spans of the Quran, corrupts them with synthetic ASR-like noise,
and measures whether the matcher finds them again.

Usage: uv run --project backend python ml/eval/text_eval.py
Writes ml/eval/reports/phase1.md. All numbers in that file come from this run.
"""

import argparse
import os
import platform
import random
import statistics
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import get_args

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from rapidfuzz import fuzz

from app.matcher.index import QuranIndex
from app.matcher.normalize import DEFAULT_CONFIG, HamzaMode, NormalizationConfig, tokenize
from app.matcher.quran_data import QuranData, load_quran
from app.matcher.search import AyahMatcher, MatchResult

DATA_DIR = REPO / "ml" / "data" / "tanzil"
REPORT = REPO / "ml" / "eval" / "reports" / "phase1.md"

SEED = 20261116
N_SPANS = 2000
MIN_LEN, MAX_LEN = 4, 25
WER_LEVELS = (0.0, 0.05, 0.10, 0.15, 0.20)
LONG_SPAN = 8
DEFAULT_DELTA = 2.0
MAX_FALSE_ACCEPT = 0.01  # on hard negatives, used to pick MATCH_THRESHOLD

# Letters ASR tends to confuse (from the build brief), both directions.
CONFUSION_PAIRS = ("ثس", "ذز", "ضد", "ظز", "قك", "هح")
CONFUSIONS: dict[str, list[str]] = {}
for a, b in CONFUSION_PAIRS:
    CONFUSIONS.setdefault(a, []).append(b)
    CONFUSIONS.setdefault(b, []).append(a)


# --------------------------------------------------------------------- noise


def substitute(word: str, rng: random.Random, alphabet: str) -> str:
    """Swap one letter: a confusable one if the word has any, else a random one."""
    slots = [i for i, ch in enumerate(word) if ch in CONFUSIONS]
    if slots:
        i = rng.choice(slots)
        return word[:i] + rng.choice(CONFUSIONS[word[i]]) + word[i + 1 :]
    i = rng.randrange(len(word))
    replacement = rng.choice([ch for ch in alphabet if ch != word[i]])
    return word[:i] + replacement + word[i + 1 :]


def add_noise(
    words: list[str], wer: float, rng: random.Random, vocab: list[str], alphabet: str
) -> tuple[list[str], int]:
    """Returns (noisy words, number of word-level edits applied)."""
    out: list[str] = []
    edits = 0
    i = 0
    while i < len(words):
        word = words[i]
        if rng.random() >= wer:
            out.append(word)
            i += 1
            continue
        edits += 1
        op = rng.choice(("sub", "sub", "del", "ins", "merge", "split"))
        if op == "del" and len(words) > 2:
            pass
        elif op == "ins":
            out.extend((word, rng.choice(vocab)))
        elif op == "merge" and i + 1 < len(words):
            out.append(word + words[i + 1])
            i += 1
        elif op == "split" and len(word) >= 4:
            cut = rng.randint(2, len(word) - 2)
            out.extend((word[:cut], word[cut:]))
        else:
            out.append(substitute(word, rng, alphabet))
        i += 1
    return (out or words[:1]), edits


# ------------------------------------------------------------------- samples


@dataclass
class Span:
    start: int
    end: int  # inclusive global word index
    words: list[str]
    primary: int  # ayah index with the most words in the span
    occurrences: int  # how many times this exact word sequence occurs
    occurrence_ayahs: set[int] = field(default_factory=set)
    crosses_ayah: bool = False
    crosses_surah: bool = False

    @property
    def unique(self) -> bool:
        return self.occurrences == 1


def primary_ayah(index: QuranIndex, start: int, end: int) -> int:
    counts = Counter(index.word_ayah[p] for p in range(start, end + 1))
    return min(counts, key=lambda a: (-counts[a], a))


def make_span(index: QuranIndex, start: int, length: int) -> Span:
    end = start + length - 1
    starts = index.occurrences(start, end)
    first, last = index.word_ayah[start], index.word_ayah[end]
    return Span(
        start=start,
        end=end,
        words=index.words[start : end + 1],
        primary=primary_ayah(index, start, end),
        occurrences=len(starts),
        occurrence_ayahs={primary_ayah(index, s, s + length - 1) for s in starts},
        crosses_ayah=first != last,
        crosses_surah=index.ayahs[first].surah != index.ayahs[last].surah,
    )


def sample_spans(index: QuranIndex, rng: random.Random, n: int) -> list[Span]:
    spans = []
    for _ in range(n):
        length = rng.randint(MIN_LEN, MAX_LEN)
        start = rng.randrange(0, len(index.words) - length + 1)
        spans.append(make_span(index, start, length))
    return spans


# ------------------------------------------------------------------- scoring


@dataclass
class Outcome:
    span: Span
    result: MatchResult
    millis: float

    @property
    def top1(self) -> bool:
        return self.result.best is not None and self.result.best.ayah_idx == self.span.primary

    @property
    def located(self) -> bool:
        """The best span overlaps the true span by more than half of the shorter one."""
        best = self.result.best
        if best is None:
            return False
        shared = min(best.end_idx, self.span.end) - max(best.start_idx, self.span.start) + 1
        shorter = min(best.end_idx - best.start_idx, self.span.end - self.span.start) + 1
        return shared * 2 > shorter

    @property
    def top3(self) -> bool:
        return self.span.primary in {c.ayah_idx for c in self.result.ranked[:3]}

    @property
    def truth_listed(self) -> bool:
        """The true location is among the locations offered to the user."""
        if self.result.status == "match":
            return self.top1
        return self.span.primary in {c.ayah_idx for c in self.result.alternatives}


def run(matcher: AyahMatcher, span: Span, query: list[str]) -> Outcome:
    started = time.perf_counter()
    result = matcher.search_words(query)
    return Outcome(span, result, (time.perf_counter() - started) * 1000)


def pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "n/a"


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


# -------------------------------------------------------------------- report


def table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def hamza_comparison(quran: QuranData, rng_seed: int) -> tuple[str, dict[str, float]]:
    """Compare standalone-hamza settings on data. Returns (markdown, top-1 by mode)."""
    rows = []
    top1_by_mode: dict[str, float] = {}
    for mode in get_args(HamzaMode):
        config = NormalizationConfig(mode)
        index = QuranIndex.build(quran, config)
        same_ayahs = 0
        similarity = []
        for ayah in quran.ayahs:
            simple = " ".join(tokenize(ayah.text_simple, config))
            uthmani = " ".join(tokenize(ayah.text_uthmani, config))
            same_ayahs += simple == uthmani
            similarity.append(fuzz.ratio(simple, uthmani))
        groups = set(index.duplicate_groups.values())

        rng = random.Random(rng_seed)  # noqa: S311 - reproducible eval, not security
        spans = [s for s in sample_spans(index, rng, N_SPANS) if s.unique]
        matcher = AyahMatcher(index, match_threshold=0, ambiguity_delta=DEFAULT_DELTA)
        vocab, alphabet = list(index.unigrams), "".join(sorted(set("".join(index.unigrams))))
        hits = sum(
            run(matcher, s, add_noise(s.words, 0.10, rng, vocab, alphabet)[0]).top1 for s in spans
        )
        top1_by_mode[mode] = hits / len(spans)
        rows.append(
            [
                f"`{mode}`",
                f"{len(index.unigrams):,}",
                str(len(groups)),
                str(sum(len(g) for g in groups)),
                pct(same_ayahs, len(quran.ayahs)),
                f"{statistics.mean(similarity):.2f}",
                pct(hits, len(spans)),
            ]
        )
    header = [
        "Setting",
        "Vocabulary",
        "Duplicate groups",
        "Ayahs in groups",
        "Uthmani = simple (ayahs)",
        "Uthmani vs simple (mean char similarity)",
        "Top-1 @ WER 10% (unique spans)",
    ]
    return table(header, rows), top1_by_mode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPORT)
    args = parser.parse_args()

    quran = load_quran(DATA_DIR)
    index = QuranIndex.build(quran, DEFAULT_CONFIG)
    vocab = list(index.unigrams)
    alphabet = "".join(sorted(set("".join(vocab))))
    rng = random.Random(SEED)  # noqa: S311 - reproducible eval, not security
    spans = sample_spans(index, rng, N_SPANS)
    queries = {
        wer: [add_noise(s.words, wer, rng, vocab, alphabet) for s in spans] for wer in WER_LEVELS
    }

    # ---- pass 1: raw scores (no threshold) to calibrate MATCH_THRESHOLD ----
    raw = AyahMatcher(index, match_threshold=0, ambiguity_delta=DEFAULT_DELTA)
    positive_scores = {
        wer: [
            (r.best.score if (r := raw.search_words(q)).best else 0.0, s)
            for s, (q, _) in zip(spans, queries[wer], strict=True)
        ]
        for wer in WER_LEVELS
    }
    negatives = []
    for _ in range(N_SPANS):
        length = rng.randint(MIN_LEN, MAX_LEN)
        words = [index.words[rng.randrange(len(index.words))] for _ in range(length)]
        result = raw.search_words(words)
        negatives.append((result.best.score if result.best else 0.0, length))

    def false_accept(threshold: int, min_len: int = 0) -> float:
        pool = [score for score, length in negatives if length >= min_len]
        return sum(score >= threshold for score in pool) / len(pool)

    def false_reject(threshold: int, wer: float, min_len: int = 0) -> float:
        pool = [score for score, s in positive_scores[wer] if len(s.words) >= min_len]
        return sum(score < threshold for score in pool) / len(pool)

    threshold = next(t for t in range(40, 101) if false_accept(t) <= MAX_FALSE_ACCEPT)
    threshold_rows = [
        [
            ("**" + str(t) + "**") if t == threshold else str(t),
            f"{100 * false_accept(t):.1f}%",
            f"{100 * false_accept(t, LONG_SPAN):.1f}%",
            *(f"{100 * false_reject(t, wer):.1f}%" for wer in WER_LEVELS),
        ]
        for t in sorted({50, 55, 60, 65, 70, 75, 80, 85, 90, threshold})
    ]

    # ---- pass 2: final metrics with the chosen threshold ----
    matcher = AyahMatcher(index, match_threshold=threshold, ambiguity_delta=DEFAULT_DELTA)
    outcomes = {
        wer: [run(matcher, s, q) for s, (q, _) in zip(spans, queries[wer], strict=True)]
        for wer in WER_LEVELS
    }

    accuracy_rows, long_rows, status_rows, ambiguous_rows = [], [], [], []
    for wer in WER_LEVELS:
        outs = outcomes[wer]
        edits = sum(e for _, e in queries[wer])
        realised = edits / sum(len(s.words) for s in spans)
        unique = [o for o in outs if o.span.unique]
        long_unique = [o for o in unique if len(o.span.words) >= LONG_SPAN]
        short_unique = [o for o in unique if len(o.span.words) < LONG_SPAN]
        label = f"{round(wer * 100)}%"

        accuracy_rows.append(
            [
                label,
                f"{100 * realised:.1f}%",
                str(len(unique)),
                pct(sum(o.top1 for o in unique), len(unique)),
                pct(sum(o.top3 for o in unique), len(unique)),
                pct(sum(o.located for o in unique), len(unique)),
                pct(sum(o.truth_listed for o in unique), len(unique)),
            ]
        )
        long_rows.append(
            [
                label,
                str(len(long_unique)),
                pct(sum(o.top1 for o in long_unique), len(long_unique)),
                pct(sum(o.top3 for o in long_unique), len(long_unique)),
                str(len(short_unique)),
                pct(sum(o.top1 for o in short_unique), len(short_unique)),
                pct(sum(o.top3 for o in short_unique), len(short_unique)),
            ]
        )
        counts = Counter(o.result.status for o in unique)
        flagged = [o for o in unique if o.result.status == "ambiguous"]
        status_rows.append(
            [
                label,
                pct(counts["match"], len(unique)),
                pct(counts["ambiguous"], len(unique)),
                pct(counts["no_match"], len(unique)),
                pct(sum(o.truth_listed for o in flagged), len(flagged)),
                pct(
                    sum(o.result.status == "match" and not o.top1 for o in unique),
                    len(unique),
                ),
            ]
        )
        repeated = [o for o in outs if not o.span.unique]
        ambiguous_rows.append(
            [
                label,
                str(len(repeated)),
                pct(sum(o.result.status == "ambiguous" for o in repeated), len(repeated)),
                pct(sum(o.truth_listed for o in repeated), len(repeated)),
                pct(
                    sum(o.result.repeated_count == o.span.occurrences for o in repeated),
                    len(repeated),
                ),
                pct(sum(o.result.status == "match" for o in repeated), len(repeated)),
            ]
        )

    # ---- ambiguity delta sweep at WER 10% ----
    delta_rows = []
    for delta in (0.0, 1.0, 2.0, 3.0, 5.0):
        m = AyahMatcher(index, match_threshold=threshold, ambiguity_delta=delta)
        outs = [run(m, s, q) for s, (q, _) in zip(spans, queries[0.10], strict=True)]
        unique = [o for o in outs if o.span.unique]
        delta_rows.append(
            [
                f"{delta:g}",
                pct(sum(o.result.status == "ambiguous" for o in unique), len(unique)),
                pct(sum(o.result.status == "match" and not o.top1 for o in unique), len(unique)),
                pct(sum(o.truth_listed for o in unique), len(unique)),
            ]
        )

    # ---- isti'adha / basmala at the start of a clip ----
    prefix_rows = []
    basmala, istiadha = list(index.basmala_words), list(index.istiadha_words)
    surah_starts = [(i, a) for i, a in enumerate(index.ayahs) if a.ayah == 1]
    for kind in ("isti'adha", "basmala", "isti'adha+basmala"):
        for wer in (0.0, 0.10):
            total = correct = detected = 0
            for _ in range(300):
                ayah_idx, ayah = rng.choice(surah_starts)
                if "basmala" in kind and ayah.surah in (1, 9):
                    continue  # 1:1 is the basmala itself; surah 9 has none
                length = rng.randint(MIN_LEN, 20)
                span = make_span(index, index.ayah_start[ayah_idx], length)
                lead = (istiadha if "isti" in kind else []) + (basmala if "basm" in kind else [])
                query, _ = add_noise(lead + span.words, wer, rng, vocab, alphabet)
                outcome = run(matcher, span, query)
                total += 1
                correct += outcome.truth_listed
                detected += outcome.result.prefix_detected == kind
            prefix_rows.append(
                [
                    kind,
                    f"{round(wer * 100)}%",
                    str(total),
                    pct(correct, total),
                    pct(detected, total),
                ]
            )

    # ---- basmala in the middle of a clip (end of surah N into surah N+1) ----
    middle_rows = []
    for wer in (0.0, 0.10):
        total = correct = 0
        for _ in range(300):
            ayah_idx, ayah = rng.choice(surah_starts)
            if ayah.surah in (1, 9):
                continue
            boundary = index.ayah_start[ayah_idx]
            before, after = rng.randint(3, 10), rng.randint(3, 10)
            span = make_span(index, boundary - before, before + after)
            words = span.words[:before] + basmala + span.words[before:]
            outcome = run(matcher, span, add_noise(words, wer, rng, vocab, alphabet)[0])
            total += 1
            # Either side of the surah boundary is a correct answer here.
            ok = {index.word_ayah[boundary - 1], index.word_ayah[boundary], span.primary}
            listed = (
                {outcome.result.best.ayah_idx}
                if outcome.result.status == "match" and outcome.result.best
                else {c.ayah_idx for c in outcome.result.alternatives}
            )
            correct += bool(ok & listed)
        middle_rows.append([f"{round(wer * 100)}%", str(total), pct(correct, total)])

    # ---- latency ----
    latency_rows = []
    for name, selector in (
        ("all queries", lambda o: True),
        ("4-7 words", lambda o: len(o.span.words) < LONG_SPAN),
        ("8-15 words", lambda o: LONG_SPAN <= len(o.span.words) <= 15),
        ("16-25 words", lambda o: len(o.span.words) > 15),
    ):
        ms = [o.millis for outs in outcomes.values() for o in outs if selector(o)]
        latency_rows.append(
            [
                name,
                f"{len(ms):,}",
                f"{percentile(ms, 0.50):.2f}",
                f"{percentile(ms, 0.95):.2f}",
                f"{percentile(ms, 0.99):.2f}",
                f"{max(ms):.2f}",
            ]
        )
    all_ms = [o.millis for outs in outcomes.values() for o in outs]
    p95 = percentile(all_ms, 0.95)

    hamza_table, hamza_top1 = hamza_comparison(quran, SEED)

    # ---- targets ----
    at10 = [o for o in outcomes[0.10] if o.span.unique and len(o.span.words) >= LONG_SPAN]
    top1_at10 = sum(o.top1 for o in at10) / len(at10)
    crossing = sum(s.crosses_ayah for s in spans)
    crossing_surah = sum(s.crosses_surah for s in spans)
    n_unique = sum(s.unique for s in spans)
    groups = set(index.duplicate_groups.values())

    def verdict(ok: bool) -> str:
        return "met" if ok else "NOT met"

    report = f"""# Phase 1 — text-only matcher evaluation

Generated by `ml/eval/text_eval.py`. Every number below comes from that run;
nothing is estimated. Re-run with `make eval`.

- Machine: {platform.machine()}, {os.cpu_count()} logical CPUs, Python {platform.python_version()}
- Seed: {SEED}
- Normalization: standalone hamza = `{DEFAULT_CONFIG.standalone_hamza}`
- Index: {len(index.words):,} words, vocabulary {len(index.unigrams):,},
  {len(index.bigrams):,} bigrams, {len(index.trigrams):,} trigrams,
  {len(groups)} duplicate-ayah groups (largest {max(len(g) for g in groups)} ayahs)

## Targets

| Target | Result | Verdict |
| --- | --- | --- |
| Top-1 ≥ 95% at WER 10% for spans ≥ 8 words | {100 * top1_at10:.1f}% ({len(at10)} unique spans) | {verdict(top1_at10 >= 0.95)} |
| p95 search latency < 50 ms | {p95:.2f} ms | {verdict(p95 < 50)} |

## Sample

{N_SPANS:,} spans, length uniform {MIN_LEN}–{MAX_LEN} words, start uniform over the
global word sequence. {crossing:,} cross an ayah boundary ({pct(crossing, N_SPANS)}),
{crossing_surah} cross a surah boundary.

{n_unique:,} spans are **unique** (their exact word sequence occurs once in the
Quran). The other {N_SPANS - n_unique} are **repeated** phrases: for those, no
matcher can know the location from the text alone, so they are scored
separately on whether they are reported as ambiguous with the true location listed.

Noise per word, at the nominal rate: substitution of a similar letter
({", ".join(a + "/" + b for a, b in CONFUSION_PAIRS)}; a random letter if the
word has none), deletion, insertion of a random Quran word, merge with the next
word, split in two. Substitution is twice as likely as each other operation.

## Accuracy on unique spans

Top-1 and Top-3 are strict: the reported *primary ayah* (the ayah with the most
matched words) must equal the true one. "Passage located" is looser: the best
span overlaps the true span, even if a word at the edge tipped the primary ayah
to a neighbour. "Truth offered" counts a result as good when it is a correct match, or an
ambiguous result that lists the true location among the choices.

{table(["Nominal WER", "Realised edit rate", "Spans", "Top-1", "Top-3", "Passage located", "Truth offered"], accuracy_rows)}

By span length:

{table(["Nominal WER", f"Spans ≥ {LONG_SPAN} words", "Top-1", "Top-3", f"Spans < {LONG_SPAN} words", "Top-1", "Top-3"], long_rows)}

## Status breakdown on unique spans

"Wrong match" is the harmful case: status `match` pointing at the wrong ayah.

{table(["Nominal WER", "match", "ambiguous", "no_match", "Truth listed when ambiguous", "Wrong match"], status_rows)}

## Ambiguity handling on repeated phrases

{table(["Nominal WER", "Spans", "Reported ambiguous", "True location listed", "repeated_count exact", "Reported as plain match"], ambiguous_rows)}

## `AMBIGUITY_DELTA` sweep (WER 10%, unique spans)

{table(["Delta", "Flagged ambiguous", "Wrong match", "Truth offered"], delta_rows)}

## `MATCH_THRESHOLD` calibration

Negatives are {N_SPANS:,} random word sequences ({MIN_LEN}–{MAX_LEN} words) drawn
from the Quran's own word frequencies: text that shares its vocabulary but is
not a passage. The threshold is the lowest score at which at most
{100 * MAX_FALSE_ACCEPT:g}% of these are accepted: **{threshold}**.

{table(["Threshold", "False accept (all negatives)", f"False accept (≥ {LONG_SPAN} words)", *(f"False reject @ WER {round(w * 100)}%" for w in WER_LEVELS)], threshold_rows)}

This is provisional. Real negatives (non-Quran speech, ASR hallucinations) only
exist from Phase 2, where the threshold is re-calibrated on audio.

## Isti'adha / basmala at the start of a clip

Clips start at ayah 1 of a random surah with the prefix prepended; noise is
applied to the prefix too.

{table(["Prefix", "Nominal WER", "Clips", "Truth offered", "Prefix reported correctly"], prefix_rows)}

## Basmala in the middle of a clip

The end of one surah, then a basmala, then the start of the next. The basmala
is not part of the indexed word sequence there, so the matcher also tries the
query with a mid-clip basmala removed. Either side of the surah boundary counts
as correct.

{table(["Nominal WER", "Clips", "Truth offered"], middle_rows)}

## Search latency (ms, single thread)

{table(["Queries", "Count", "p50", "p95", "p99", "max"], latency_rows)}

## Standalone hamza setting

Each setting builds its own index. "Uthmani = simple" is the share of ayahs
whose normalized Uthmani text equals their normalized simple text — a proxy for
robustness if the ASR model writes Uthmani-style spelling.

{hamza_table}
"""
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"hamza top-1 @ WER 10%: {hamza_top1}")
    print(f"wrote {args.out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
