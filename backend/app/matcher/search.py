"""Ayah matcher: finds where a (noisy) transcript sits in the Quran.

1. Offset voting over n-gram postings proposes start positions.
2. Each proposal is scored by character-level alignment against a text window,
   which tolerates ASR word merges and splits.
3. The aligned range is mapped back to a word span and a primary ayah.
4. The result is `match`, `ambiguous` or `no_match`.
"""

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein

from app.matcher.index import QuranIndex, WordRef
from app.matcher.normalize import tokenize

Status = Literal["match", "ambiguous", "no_match"]
Reason = Literal["too_short", "low_confidence"]
Prefix = Literal["isti'adha", "basmala", "isti'adha+basmala"]

TOP_K = 20
WINDOW_PAD = 0.30
MIN_QUERY_WORDS = 2
MAX_QUERY_WORDS = 80
PREFIX_SIMILARITY = 80.0
INTERIOR_SIMILARITY = 85.0
# Very common n-grams add noise and cost; skip postings longer than this.
MAX_POSTINGS = {3: 2000, 2: 1500, 1: 40}
VOTE_WEIGHT = {3: 3, 2: 2, 1: 1}
VOTE_SMOOTHING = 2  # words; absorbs offset drift from ASR merges/splits
MAX_ALTERNATIVES = 5


@dataclass(frozen=True)
class Candidate:
    score: float
    """0-100 character-level similarity."""
    start_idx: int
    end_idx: int
    """Global word positions, inclusive."""
    ayah_idx: int
    """Primary ayah: the one with the most covered words."""
    start: WordRef
    end: WordRef


@dataclass(frozen=True)
class MatchResult:
    status: Status
    reason: Reason | None
    best: Candidate | None
    ranked: tuple[Candidate, ...]
    """Distinct locations by descending score (best first)."""
    alternatives: tuple[Candidate, ...]
    """When ambiguous: every location the user could mean, in mushaf order."""
    repeated_count: int | None
    """When ambiguous: how many locations there are (may exceed what a UI lists)."""
    prefix_detected: Prefix | None
    query_words: int


def _no_match(reason: Reason, n_words: int, prefix: Prefix | None = None) -> MatchResult:
    return MatchResult("no_match", reason, None, (), (), None, prefix, n_words)


class AyahMatcher:
    def __init__(
        self,
        index: QuranIndex,
        match_threshold: float,
        ambiguity_delta: float,
    ) -> None:
        self.index = index
        self.match_threshold = match_threshold
        self.ambiguity_delta = ambiguity_delta
        self._postings = {1: index.unigrams, 2: index.bigrams, 3: index.trigrams}

    # ------------------------------------------------------------------ public

    def search(self, text: str) -> MatchResult:
        """Match raw text (e.g. an ASR transcript). Normalization happens here."""
        return self.search_words(tokenize(text, self.index.config))

    def search_words(self, words: list[str]) -> MatchResult:
        words = words[:MAX_QUERY_WORDS]
        if len(words) < MIN_QUERY_WORDS:
            return _no_match("too_short", len(words))

        variants = self._variants(words)
        searchable = [(prefix, v) for prefix, v in variants if len(v) >= MIN_QUERY_WORDS]
        # Nothing but an isti'adha (which is not Quran text): do not let it
        # fuzzy-match the ayah it resembles.
        only_istiadha = any(p == "isti'adha" and len(v) < MIN_QUERY_WORDS for p, v in variants)
        if only_istiadha or not searchable:
            return _no_match("too_short", len(words), variants[-1][0])

        # Variants are ordered least-modified first and only a strictly better
        # score replaces the current best, so ties keep the less-modified query
        # (Al-Fatiha 1:1, where the basmala IS the ayah, still matches).
        best_ranked: list[Candidate] = []
        best_prefix: Prefix | None = None
        for prefix, variant in searchable:
            ranked = self._rank(variant)
            if ranked and (not best_ranked or ranked[0].score > best_ranked[0].score):
                best_ranked, best_prefix = ranked, prefix

        if not best_ranked or best_ranked[0].score < self.match_threshold:
            return MatchResult(
                "no_match",
                "low_confidence",
                None,
                tuple(best_ranked),
                (),
                None,
                best_prefix,
                len(words),
            )

        best = best_ranked[0]
        alternatives = self._alternatives(best, best_ranked)
        if len(alternatives) > 1:
            return MatchResult(
                "ambiguous",
                None,
                best,
                tuple(best_ranked),
                tuple(alternatives),
                len(alternatives),
                best_prefix,
                len(words),
            )
        return MatchResult(
            "match", None, best, tuple(best_ranked), (), None, best_prefix, len(words)
        )

    # ---------------------------------------------------------------- prefixes

    def _starts_with(self, words: list[str], phrase: tuple[str, ...]) -> int:
        """How many leading words of `words` are (fuzzily) `phrase`; 0 if none."""
        target = " ".join(phrase)
        best_len, best_score = 0, PREFIX_SIMILARITY
        # ASR may merge or split a word inside the phrase.
        for length in (len(phrase), len(phrase) - 1, len(phrase) + 1):
            if 0 < length <= len(words):
                score = fuzz.ratio(" ".join(words[:length]), target)
                if score > best_score:
                    best_len, best_score = length, score
        return best_len

    def _variants(self, words: list[str]) -> list[tuple[Prefix | None, list[str]]]:
        """Query variants to search, least modified first."""
        variants: list[tuple[Prefix | None, list[str]]] = [(None, words)]
        after_istiadha = self._starts_with(words, self.index.istiadha_words)
        rest = words[after_istiadha:]
        if after_istiadha:
            variants.append(("isti'adha", rest))
        after_basmala = self._starts_with(rest, self.index.basmala_words)
        if after_basmala:
            label: Prefix = "isti'adha+basmala" if after_istiadha else "basmala"
            variants.append((label, rest[after_basmala:]))

        # A basmala recited mid-clip (end of one surah into the next) is not part
        # of the word sequence; also try each variant with it removed.
        size = len(self.index.basmala_words)
        target = " ".join(self.index.basmala_words)
        for prefix, variant in list(variants):
            for i in range(1, len(variant) - size):
                if fuzz.ratio(" ".join(variant[i : i + size]), target) >= INTERIOR_SIMILARITY:
                    variants.append((prefix, variant[:i] + variant[i + size :]))
                    break
        return variants

    # ------------------------------------------------------------------ search

    def _propose(self, words: list[str]) -> list[int]:
        """Offset voting: candidate global start positions, best first."""
        votes: defaultdict[int, int] = defaultdict(int)
        for n in (3, 2, 1):
            postings, weight, cap = self._postings[n], VOTE_WEIGHT[n], MAX_POSTINGS[n]
            for i in range(len(words) - n + 1):
                hits = postings.get(" ".join(words[i : i + n]))
                if hits is None or len(hits) > cap:
                    continue
                for pos in hits:
                    votes[pos - i] += weight
        if not votes:
            return []

        smoothed: defaultdict[int, int] = defaultdict(int)
        for start, count in votes.items():
            for shift in range(-VOTE_SMOOTHING, VOTE_SMOOTHING + 1):
                smoothed[start + shift] += count

        chosen: list[int] = []
        for start, _ in sorted(smoothed.items(), key=lambda kv: (-kv[1], kv[0])):
            if all(abs(start - other) > VOTE_SMOOTHING + 1 for other in chosen):
                chosen.append(start)
                if len(chosen) == TOP_K:
                    break
        return chosen

    def _align(self, query_text: str, n_words: int, start: int) -> Candidate | None:
        """Score one proposal and map the aligned characters back to words."""
        corpus = self.index.words
        pad = max(2, math.ceil(n_words * WINDOW_PAD))
        lo = max(0, start - pad)
        hi = min(len(corpus), start + n_words + pad)
        if lo >= hi:
            return None
        window = corpus[lo:hi]
        alignment = fuzz.partial_ratio_alignment(query_text, " ".join(window))
        if alignment is None or alignment.dest_end <= alignment.dest_start:
            return None

        # Whole words touched by the aligned character range.
        touched: list[int] = []
        cursor = 0
        for offset, word in enumerate(window):
            if cursor < alignment.dest_end and cursor + len(word) > alignment.dest_start:
                touched.append(offset)
            cursor += len(word) + 1
        if not touched:
            return None

        # partial_ratio aligns a fixed-length character window, which can spill
        # onto neighbouring words. Re-align against whole words and keep the
        # span between the first and last word that mostly matches the query.
        aligned = window[touched[0] : touched[-1] + 1]
        spaces = len(aligned)  # sink for matches on the joining spaces
        owner: list[int] = []
        for i, word in enumerate(aligned):
            owner.extend([i] * len(word))
            owner.append(spaces)
        matched = [0] * (len(aligned) + 1)
        for op in Levenshtein.opcodes(query_text, " ".join(aligned)):
            if op.tag == "equal":
                for char in range(op.dest_start, op.dest_end):
                    matched[owner[char]] += 1
        covered = [
            lo + touched[0] + i for i, word in enumerate(aligned) if matched[i] * 2 >= len(word)
        ]
        if not covered:
            return None
        return self._candidate(alignment.score, covered[0], covered[-1])

    def _candidate(self, score: float, first: int, last: int) -> Candidate:
        index = self.index
        counts: defaultdict[int, int] = defaultdict(int)
        for pos in range(first, last + 1):
            counts[index.word_ayah[pos]] += 1
        primary = min(counts, key=lambda ayah_idx: (-counts[ayah_idx], ayah_idx))
        return Candidate(score, first, last, primary, index.word_ref(first), index.word_ref(last))

    def _rank(self, words: list[str]) -> list[Candidate]:
        """Distinct candidate locations, best first."""
        query_text = " ".join(words)
        scored = [
            cand
            for start in self._propose(words)
            if (cand := self._align(query_text, len(words), start)) is not None
        ]
        scored.sort(key=lambda c: (-c.score, c.start_idx))

        distinct: list[Candidate] = []
        for cand in scored:
            if not any(_overlaps(cand, kept) for kept in distinct):
                distinct.append(cand)
        return distinct

    # --------------------------------------------------------------- ambiguity

    def _alternatives(self, best: Candidate, ranked: list[Candidate]) -> list[Candidate]:
        """All locations the query could mean. A single entry means unambiguous."""
        length = best.end_idx - best.start_idx
        # 1) The matched words occur verbatim elsewhere (refrains, repeated phrases).
        found = [
            self._candidate(best.score, start, start + length)
            for start in self.index.occurrences(best.start_idx, best.end_idx)
        ]
        # 2) A different location scores almost as well.
        for cand in ranked[1:]:
            if best.score - cand.score > self.ambiguity_delta:
                break
            if cand.score >= self.match_threshold and not any(_overlaps(cand, f) for f in found):
                found.append(cand)
        found.sort(key=lambda c: c.start_idx)
        return found


def _overlaps(a: Candidate, b: Candidate) -> bool:
    """True when two spans share more than half of the shorter one."""
    shared = min(a.end_idx, b.end_idx) - max(a.start_idx, b.start_idx) + 1
    shorter = min(a.end_idx - a.start_idx, b.end_idx - b.start_idx) + 1
    return shared * 2 > shorter
