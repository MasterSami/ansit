"""Persist and load the reciter registry and gallery in PostgreSQL (pgvector).

Postgres is the source of truth. The service loads the whole gallery into
memory at startup and scores it in NumPy (`app.speaker.gallery`): at a few
thousand vectors that is faster than a database round trip and keeps the
request path free of database latency.
"""

from typing import Any, cast

import numpy as np
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GalleryClip, Reciter, ReciterCentroid
from app.speaker.engine import EMBEDDING_DIM
from app.speaker.gallery import Gallery, Style, Voice

_REGISTRY_FIELDS = ("name_ar", "name_en", "country", "styles", "sources", "active")


async def upsert_reciters(session: AsyncSession, registry: list[dict[str, Any]]) -> None:
    """Insert or update registry entries (as in ml/registry/reciters.json)."""
    for entry in registry:
        values = {"id": entry["id"], **{k: entry[k] for k in _REGISTRY_FIELDS}}
        statement = insert(Reciter).values(**values)
        await session.execute(
            statement.on_conflict_do_update(
                index_elements=[Reciter.id],
                set_={k: statement.excluded[k] for k in _REGISTRY_FIELDS},
            )
        )


async def save_gallery(
    session: AsyncSession, gallery: Gallery, reciter_ids: set[str] | None = None
) -> None:
    """Replace the stored gallery for `reciter_ids` (default: every reciter in it).

    Adding a new reciter touches only that reciter's rows.
    """
    wanted = reciter_ids or {v.reciter_id for v in gallery.voices}
    await session.execute(delete(GalleryClip).where(GalleryClip.reciter_id.in_(wanted)))
    await session.execute(delete(ReciterCentroid).where(ReciterCentroid.reciter_id.in_(wanted)))
    for index, voice in enumerate(gallery.voices):
        if voice.reciter_id not in wanted:
            continue
        rows = np.flatnonzero(gallery.voice_of_clip == index)
        session.add_all(
            GalleryClip(
                reciter_id=voice.reciter_id,
                style=voice.style,
                embedding=gallery.embeddings[row].tolist(),
            )
            for row in rows
        )
        session.add(
            ReciterCentroid(
                reciter_id=voice.reciter_id,
                style=voice.style,
                clip_count=len(rows),
                embedding=gallery.centroids[index].tolist(),
            )
        )
    await session.flush()


async def load_gallery(session: AsyncSession) -> Gallery:
    """Load the clips of all active reciters into an in-memory gallery."""
    result = await session.execute(
        select(GalleryClip.reciter_id, GalleryClip.style, GalleryClip.embedding)
        .join(Reciter, Reciter.id == GalleryClip.reciter_id)
        .where(Reciter.active.is_(True))
        .order_by(GalleryClip.reciter_id, GalleryClip.style, GalleryClip.id)
    )
    voices: list[Voice] = []
    index_of: dict[Voice, int] = {}
    vectors: list[Any] = []
    owners: list[int] = []
    for reciter_id, style, embedding in result:
        voice = Voice(reciter_id, cast(Style, style))
        if voice not in index_of:
            index_of[voice] = len(voices)
            voices.append(voice)
        vectors.append(np.asarray(embedding, dtype=np.float32))
        owners.append(index_of[voice])
    embeddings = np.stack(vectors) if vectors else np.zeros((0, EMBEDDING_DIM), dtype=np.float32)
    return Gallery(voices, embeddings, np.asarray(owners, dtype=np.intp))


async def load_reciters(session: AsyncSession, *, only_active: bool = True) -> list[Reciter]:
    statement = select(Reciter).order_by(Reciter.id)
    if only_active:
        statement = statement.where(Reciter.active.is_(True))
    return list((await session.execute(statement)).scalars())
