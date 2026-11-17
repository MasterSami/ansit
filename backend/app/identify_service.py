"""Runs one identify request: both branches, fusion, metrics, event record.

Privacy: the clip exists only in this call's memory. Nothing here logs audio
or transcripts, and nothing writes the clip to disk.
"""

import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.errors import ApiError
from app.api.schemas import (
    AyahOut,
    CandidateOut,
    DebugOut,
    IdentifyResponse,
    ReciterAlternativeOut,
    ReciterOut,
    SpanOut,
    TimingsOut,
    WordRefOut,
)
from app.audio.decode import AudioError, Waveform
from app.core.config import Settings
from app.core.ephemeral import CandidateStore, Spans
from app.core.logging import get_logger
from app.core.metrics import (
    IDENTIFY_IN_FLIGHT,
    IDENTIFY_REJECTED,
    IDENTIFY_STAGE,
    IDENTIFY_TOTAL,
    RECITER_SIMILARITY,
    RECITER_TOTAL,
    TEXT_CONFIDENCE,
)
from app.db.models import IdentifyEvent
from app.matcher.index import QuranIndex
from app.matcher.search import Candidate
from app.pipeline import AyahIdentification
from app.services import ReciterInfo, Services
from app.speaker.gallery import ReciterResult, ReciterScore

log = get_logger(__name__)

MAX_CANDIDATES = 5
# "Listen longer": the follow-up clip starts after the first one ended. Allow a
# little overlap and the recitation that went by while the user waited.
FOLLOW_MIN_GAP = -3
FOLLOW_MAX_GAP = 80

_AUDIO_ERRORS: dict[str, tuple[int, str, str]] = {
    "too_large": (413, "audio_too_large", "The audio file is too large."),
    "too_long": (422, "audio_too_long", "The audio clip is too long."),
    "decode_failed": (422, "audio_unreadable", "The audio could not be decoded."),
    "no_audio": (422, "audio_unreadable", "The upload contains no audio."),
}


@dataclass
class _ReciterBranch:
    result: ReciterResult | None
    millis: float


class IdentifyService:
    def __init__(
        self,
        settings: Settings,
        services: Services,
        candidates: CandidateStore,
        sessions: async_sessionmaker[AsyncSession] | None,
    ) -> None:
        self.settings = settings
        self.services = services
        self.candidates = candidates
        self.sessions = sessions
        self._slots = asyncio.Semaphore(settings.max_concurrent_identify)
        # Two branches per request, plus the decode step.
        self._pool = ThreadPoolExecutor(
            max_workers=settings.max_concurrent_identify * 2 + 1, thread_name_prefix="identify"
        )
        self._background: set[asyncio.Task[None]] = set()

    def close(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)

    # ------------------------------------------------------------------ entry

    async def identify(
        self,
        data: bytes,
        *,
        client: str | None,
        app_version: str | None,
        debug: bool,
        previous_identify_id: uuid.UUID | None,
    ) -> IdentifyResponse:
        identifier, index = self.services.identifier, self.services.index
        if identifier is None or index is None:
            raise ApiError(503, "not_ready", "The service is still starting.")

        try:
            await asyncio.wait_for(
                self._slots.acquire(), timeout=self.settings.identify_queue_timeout_sec
            )
        except TimeoutError:
            IDENTIFY_REJECTED.labels("server_busy").inc()
            raise ApiError(
                503, "server_busy", "The service is busy. Try again.", {"Retry-After": "2"}
            ) from None

        started = time.perf_counter()
        loop = asyncio.get_running_loop()
        IDENTIFY_IN_FLIGHT.inc()
        try:
            try:
                clip = await loop.run_in_executor(self._pool, identifier.prepare, data)
            except AudioError as exc:
                status_code, code, message = _AUDIO_ERRORS[exc.reason]
                IDENTIFY_REJECTED.labels(code).inc()
                raise ApiError(status_code, code, message) from None

            reciter = _ReciterBranch(None, 0.0)
            if clip.rejected is not None:
                ayah = clip.rejected
            else:
                # Both branches at once, on the same waveform.
                ayah, reciter = await asyncio.gather(
                    loop.run_in_executor(self._pool, identifier.transcribe_and_match, clip),
                    loop.run_in_executor(self._pool, self._reciter_branch, clip.waveform),
                )
        finally:
            IDENTIFY_IN_FLIGHT.dec()
            self._slots.release()

        identify_id = uuid.uuid4()
        best, alternatives = await self._resolve(ayah, index, identify_id, previous_identify_id)
        timings = TimingsOut(
            **{k: round(v, 1) for k, v in ayah.timings_ms.items() if k != "total"},
            speaker=round(reciter.millis, 1),
            total=round((time.perf_counter() - started) * 1000, 1),
        )
        response = self._respond(
            identify_id, ayah, best, alternatives, index, reciter.result, timings, debug
        )
        stages = {*ayah.timings_ms, "total"} | ({"speaker"} if reciter.result else set())
        self._observe(response, ayah, stages, client, app_version)
        return response

    # --------------------------------------------------------------- branches

    def _reciter_branch(self, waveform: Waveform) -> _ReciterBranch:
        speaker, gallery = self.services.speaker, self.services.gallery
        if speaker is None or gallery is None:
            return _ReciterBranch(None, 0.0)
        started = time.perf_counter()
        result = gallery.identify(
            speaker.embed(waveform),
            self.settings.reciter_threshold,
            self.settings.reciter_min_margin,
        )
        return _ReciterBranch(result, (time.perf_counter() - started) * 1000)

    async def _resolve(
        self,
        ayah: AyahIdentification,
        index: QuranIndex,
        identify_id: uuid.UUID,
        previous_id: uuid.UUID | None,
    ) -> tuple[Candidate | None, list[Candidate]]:
        """Returns (best, alternatives). Uses an earlier ambiguous result, when the
        client names one, to settle which location this clip continues from."""
        match = ayah.match
        if match is None or match.best is None or ayah.status == "no_match":
            return None, []
        best, alternatives = match.best, list(match.alternatives)

        if previous_id is not None:
            earlier = await self.candidates.get(str(previous_id))
            if earlier:
                options = alternatives or [best]
                following = [
                    cand
                    for cand in options
                    if any(
                        FOLLOW_MIN_GAP <= cand.start_idx - last <= FOLLOW_MAX_GAP
                        for _, last in earlier
                    )
                ]
                if len(following) == 1:
                    best, alternatives = following[0], []
                elif following:
                    best, alternatives = following[0], following

        if len(alternatives) > 1:
            spans: Spans = [(c.start_idx, c.end_idx) for c in alternatives]
            await self.candidates.put(str(identify_id), spans)
        return best, alternatives

    # --------------------------------------------------------------- response

    def _respond(
        self,
        identify_id: uuid.UUID,
        ayah: AyahIdentification,
        best: Candidate | None,
        alternatives: list[Candidate],
        index: QuranIndex,
        reciter: ReciterResult | None,
        timings: TimingsOut,
        debug: bool,
    ) -> IdentifyResponse:
        debug_out = None
        if debug and self.settings.allow_debug:
            words = " ".join(index_tokenize(index, ayah.asr.text)) if ayah.asr is not None else None
            debug_out = DebugOut(
                transcript_normalized=words,
                prefix_detected=ayah.match.prefix_detected if ayah.match else None,
            )

        if best is None:
            return IdentifyResponse(
                id=identify_id,
                status="no_match",
                reason=ayah.reason or "low_confidence",
                timings_ms=timings,
                debug=debug_out,
            )

        ambiguous = len(alternatives) > 1
        return IdentifyResponse(
            id=identify_id,
            status="ambiguous" if ambiguous else "match",
            ayah=ayah_out(index, best.ayah_idx),
            span=SpanOut(start=WordRefOut(**vars(best.start)), end=WordRefOut(**vars(best.end))),
            text_confidence=round(best.score / 100, 4),
            candidates=[candidate_out(index, cand) for cand in alternatives[:MAX_CANDIDATES]]
            if ambiguous
            else [],
            repeated_count=len(alternatives) if ambiguous else None,
            reciter=self._reciter_out(reciter),
            timings_ms=timings,
            debug=debug_out,
        )

    def _reciter_out(self, result: ReciterResult | None) -> ReciterOut:
        if result is None or result.best is None:
            return ReciterOut(status="unknown")
        known = self.services.reciters

        def alternative(score: ReciterScore) -> ReciterAlternativeOut | None:
            info = known.get(score.reciter_id)
            if info is None:
                return None
            return ReciterAlternativeOut(
                id=info.id,
                name_ar=info.name_ar,
                name_en=info.name_en,
                style=score.style,
                similarity=round(score.similarity, 4),
            )

        info: ReciterInfo | None = known.get(result.best.reciter_id)
        if result.status == "identified" and info is not None:
            others = [alt for s in result.alternatives if (alt := alternative(s)) is not None]
            return ReciterOut(
                status="identified",
                id=info.id,
                name_ar=info.name_ar,
                name_en=info.name_en,
                style=result.best.style,
                similarity=round(result.best.similarity, 4),
                alternatives=others[:2],
            )
        # Unknown: no name is asserted; the best guesses are offered as "may also be".
        guesses = [alt for s in (result.best, *result.alternatives) if (alt := alternative(s))]
        return ReciterOut(
            status="unknown",
            similarity=round(result.best.similarity, 4),
            alternatives=guesses[:2],
        )

    # ---------------------------------------------------------- observability

    def _observe(
        self,
        response: IdentifyResponse,
        ayah: AyahIdentification,
        stages: set[str],
        client: str | None,
        app_version: str | None,
    ) -> None:
        IDENTIFY_TOTAL.labels(response.status, response.reason or "", client or "unknown").inc()
        for stage, millis in response.timings_ms.model_dump().items():
            if stage in stages:  # only stages that actually ran
                IDENTIFY_STAGE.labels(stage).observe(millis / 1000)
        if response.text_confidence is not None:
            TEXT_CONFIDENCE.observe(response.text_confidence)
        reciter = response.reciter
        if reciter is not None:
            RECITER_TOTAL.labels(reciter.status).inc()
            if reciter.similarity is not None:
                RECITER_SIMILARITY.labels(reciter.status).observe(reciter.similarity)

        # No transcript and no audio in the log line, by design.
        log.info(
            "identify",
            identify_id=str(response.id),
            status=response.status,
            reason=response.reason,
            reciter_status=reciter.status if reciter else None,
            clip_sec=round(ayah.clip_sec, 2),
            total_ms=response.timings_ms.total,
            client=client,
        )
        if self.sessions is not None:
            event = IdentifyEvent(
                id=response.id,
                status=response.status,
                reason=response.reason,
                text_confidence=response.text_confidence,
                repeated_count=response.repeated_count,
                reciter_status=reciter.status if reciter else None,
                reciter_id=reciter.id if reciter else None,
                reciter_similarity=reciter.similarity if reciter else None,
                clip_sec=round(ayah.clip_sec, 3),
                speech_sec=round(ayah.speech_sec, 3),
                timings_ms=response.timings_ms.model_dump(),
                client=client,
                app_version=app_version,
            )
            task = asyncio.create_task(self._store_event(event))
            self._background.add(task)
            task.add_done_callback(self._background.discard)

    async def _store_event(self, event: IdentifyEvent) -> None:
        assert self.sessions is not None  # noqa: S101 - checked by the caller
        try:
            async with self.sessions() as session:
                session.add(event)
                await session.commit()
        except (SQLAlchemyError, OSError) as exc:
            log.warning("identify_event_not_stored", error=type(exc).__name__)

    async def drain(self) -> None:
        """Wait for pending event writes (used at shutdown and in tests)."""
        if self._background:
            await asyncio.gather(*self._background, return_exceptions=True)


# ------------------------------------------------------------------- helpers


def index_tokenize(index: QuranIndex, text: str) -> list[str]:
    from app.matcher.normalize import tokenize

    return tokenize(text, index.config)


def ayah_out(index: QuranIndex, ayah_idx: int) -> AyahOut:
    ayah = index.ayahs[ayah_idx]
    surah = index.surahs[ayah.surah - 1]
    return AyahOut(
        surah=ayah.surah,
        surah_name_ar=surah.name_ar,
        surah_name_en=surah.name_en,
        ayah=ayah.ayah,
        text_uthmani=ayah.text_uthmani,
        juz=ayah.juz,
        page=ayah.page,
        revelation=surah.revelation,
        ayah_count=surah.ayah_count,
    )


def candidate_out(index: QuranIndex, cand: Candidate) -> CandidateOut:
    ayah = index.ayahs[cand.ayah_idx]
    previous = index.ayahs[cand.ayah_idx - 1] if ayah.ayah > 1 else None
    return CandidateOut(
        surah=ayah.surah,
        surah_name_ar=index.surahs[ayah.surah - 1].name_ar,
        ayah=ayah.ayah,
        score=round(cand.score / 100, 4),
        context_before=previous.text_uthmani if previous is not None else None,
    )
