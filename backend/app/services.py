"""Everything loaded once at startup: Quran index, models, gallery, registry.

Each part is a readiness task, so `/readyz` reports what is still loading or
failed. Tests build a `Services` object directly with scripted engines.
"""

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.asr.guards import GuardConfig
from app.audio.vad import SpeechDetector
from app.core.config import Settings
from app.core.logging import get_logger
from app.core.readiness import StartupTask
from app.db.models import GalleryClip
from app.matcher.index import QuranIndex
from app.matcher.search import AyahMatcher
from app.pipeline import AudioLimits, AyahIdentifier
from app.speaker.engine import SpeakerEngine
from app.speaker.gallery import Gallery
from app.speaker.store import load_gallery, load_reciters

log = get_logger(__name__)


@dataclass(frozen=True)
class ReciterInfo:
    id: str
    name_ar: str
    name_en: str
    country: str | None
    styles: tuple[str, ...]
    sources: dict[str, Any]

    @classmethod
    def from_entry(cls, entry: dict[str, Any]) -> "ReciterInfo":
        return cls(
            id=entry["id"],
            name_ar=entry["name_ar"],
            name_en=entry["name_en"],
            country=entry.get("country"),
            styles=tuple(entry["styles"]),
            sources=dict(entry["sources"]),
        )


@dataclass
class Services:
    index: QuranIndex | None = None
    identifier: AyahIdentifier | None = None
    speaker: SpeakerEngine | None = None
    gallery: Gallery | None = None
    reciters: dict[str, ReciterInfo] = field(default_factory=dict)


def audio_limits(settings: Settings) -> AudioLimits:
    return AudioLimits(
        max_upload_bytes=int(settings.max_upload_mb * 1024 * 1024),
        min_clip_sec=settings.min_clip_sec,
        max_clip_sec=settings.max_clip_sec,
        min_speech_sec=settings.min_speech_sec,
        trim_silence=settings.vad_trim_silence,
    )


def guard_config(settings: Settings) -> GuardConfig:
    return GuardConfig(
        max_no_speech_prob=settings.asr_max_no_speech_prob,
        min_avg_logprob=settings.asr_min_avg_logprob,
        max_compression_ratio=settings.asr_max_compression_ratio,
    )


def build_startup_tasks(
    settings: Settings,
    services: Services,
    sessions: async_sessionmaker[AsyncSession] | None,
) -> list[StartupTask]:
    """Loaders in dependency order. Model loading is blocking, so it runs in a thread."""

    async def load_index() -> None:
        services.index = await asyncio.to_thread(QuranIndex.load, Path(settings.quran_index_path))

    async def load_asr() -> None:
        from app.asr.faster_whisper_engine import FasterWhisperEngine

        if not settings.asr_model_path:
            raise RuntimeError("ASR_MODEL_PATH is not set")
        if services.index is None:
            raise RuntimeError("the Quran index did not load")

        def build() -> AyahIdentifier:
            engine = FasterWhisperEngine(
                settings.asr_model_path or "",
                device=settings.asr_device,
                compute_type=settings.asr_compute_type,
                cpu_threads=settings.cpu_threads_asr,
                beam_size=settings.asr_beam_size,
                num_workers=settings.max_concurrent_identify,
            )
            engine.warm_up()
            vad = SpeechDetector(threshold=settings.vad_threshold)
            vad.warm_up()
            assert services.index is not None  # noqa: S101 - checked above
            matcher = AyahMatcher(
                services.index, settings.match_threshold, settings.ambiguity_delta
            )
            return AyahIdentifier(
                engine, matcher, vad, audio_limits(settings), guard_config(settings)
            )

        services.identifier = await asyncio.to_thread(build)

    async def load_speaker() -> None:
        from app.speaker.engine import OnnxSpeakerEngine

        def build() -> OnnxSpeakerEngine:
            engine = OnnxSpeakerEngine(
                settings.speaker_model_path, cpu_threads=settings.cpu_threads_speaker
            )
            engine.warm_up()
            return engine

        services.speaker = await asyncio.to_thread(build)

    async def load_reciter_gallery() -> None:
        gallery, reciters, source = None, {}, "none"
        if sessions is not None:
            try:
                async with sessions() as session:
                    count = await session.scalar(select(func.count()).select_from(GalleryClip))
                    if count:
                        gallery = await load_gallery(session)
                        reciters = {
                            r.id: ReciterInfo(
                                r.id, r.name_ar, r.name_en, r.country, tuple(r.styles), r.sources
                            )
                            for r in await load_reciters(session)
                        }
                        source = "database"
            except (SQLAlchemyError, OSError) as exc:
                log.warning("gallery_database_unavailable", error=type(exc).__name__)
        if gallery is None and settings.gallery_path and settings.registry_path:
            gallery_file, registry_file = settings.gallery_path, settings.registry_path

            def from_files() -> tuple[Gallery, dict[str, ReciterInfo]]:
                entries = json.loads(Path(registry_file).read_text(encoding="utf-8"))
                known = {e["id"]: ReciterInfo.from_entry(e) for e in entries if e.get("active")}
                return Gallery.load(Path(gallery_file)), known

            gallery, reciters = await asyncio.to_thread(from_files)
            source = "files"
        if gallery is None:
            raise RuntimeError("no reciter gallery: load one into the database or set GALLERY_PATH")
        missing = {v.reciter_id for v in gallery.voices} - set(reciters)
        if missing:
            raise RuntimeError(f"gallery reciters missing from the registry: {sorted(missing)}")
        services.gallery, services.reciters = gallery, reciters
        log.info(
            "gallery_loaded",
            source=source,
            reciters=len({v.reciter_id for v in gallery.voices}),
            voices=len(gallery.voices),
            clips=len(gallery.embeddings),
        )

    tasks = [StartupTask("quran_index", load_index), StartupTask("asr_model", load_asr)]
    if settings.reciter_enabled:
        tasks += [
            StartupTask("speaker_model", load_speaker),
            StartupTask("reciter_gallery", load_reciter_gallery),
        ]
    return tasks
