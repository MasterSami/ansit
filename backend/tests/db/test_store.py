"""Registry and gallery persistence against a real PostgreSQL with pgvector.

Set TEST_DATABASE_URL to run (CI does). The tests create and drop their own
schema, so point it at a throwaway database.
"""

import os
from collections.abc import AsyncIterator
from typing import Any

import numpy as np
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.db.models import Base, GalleryClip, Reciter, ReciterCentroid
from app.speaker.engine import EMBEDDING_DIM, l2_normalize
from app.speaker.gallery import Gallery, Voice
from app.speaker.store import load_gallery, load_reciters, save_gallery, upsert_reciters

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


def _require_database() -> str:
    if DATABASE_URL:
        return DATABASE_URL
    message = "TEST_DATABASE_URL is not set"
    if os.environ.get("ANSIT_REQUIRE_DB") == "1":
        pytest.fail(message)  # CI must never silently skip these
    pytest.skip(message)


async def _reset(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(_require_database())
    await _reset(engine)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        yield db
    await _reset(engine)
    await engine.dispose()


def entry(reciter_id: str, **overrides: Any) -> dict[str, Any]:
    return {
        "id": reciter_id,
        "name_ar": f"name-ar-{reciter_id}",
        "name_en": f"Name {reciter_id}",
        "country": None,
        "styles": ["murattal"],
        "sources": {"everyayah": [{"folder": f"{reciter_id}_64kbps", "style": "murattal"}]},
        "active": True,
        **overrides,
    }


def gallery_of(spec: dict[Voice, int], seed: int = 0) -> Gallery:
    rng = np.random.default_rng(seed)
    voices = list(spec)
    vectors = [
        l2_normalize(rng.standard_normal(EMBEDDING_DIM)) for n in spec.values() for _ in range(n)
    ]
    owners = [i for i, n in enumerate(spec.values()) for _ in range(n)]
    return Gallery(voices, np.stack(vectors), np.asarray(owners, dtype=np.intp))


A, A_MUJ, B = Voice("a", "murattal"), Voice("a", "mujawwad"), Voice("b", "murattal")


async def test_round_trip(session: AsyncSession) -> None:
    await upsert_reciters(session, [entry("a", styles=["mujawwad", "murattal"]), entry("b")])
    gallery = gallery_of({A: 4, A_MUJ: 3, B: 5})
    await save_gallery(session, gallery)
    await session.commit()

    loaded = await load_gallery(session)
    assert set(loaded.voices) == {A, A_MUJ, B}
    assert len(loaded.embeddings) == 12
    assert np.allclose(np.linalg.norm(loaded.embeddings, axis=1), 1.0, atol=1e-5)
    query = gallery.embeddings[0]
    original = {(r.reciter_id, r.style): r.similarity for r in gallery.rank(query)}
    restored = {(r.reciter_id, r.style): r.similarity for r in loaded.rank(query)}
    assert restored.keys() == original.keys()
    for key, value in original.items():
        assert restored[key] == pytest.approx(value, abs=1e-5)

    centroids = (await session.execute(select(ReciterCentroid))).scalars().all()
    assert {(c.reciter_id, c.style): c.clip_count for c in centroids} == {
        ("a", "murattal"): 4,
        ("a", "mujawwad"): 3,
        ("b", "murattal"): 5,
    }
    stored = np.asarray(next(c.embedding for c in centroids if c.reciter_id == "b"))
    assert np.allclose(stored, gallery.centroids[gallery.voices.index(B)], atol=1e-5)


async def test_registry_upsert_updates_in_place(session: AsyncSession) -> None:
    await upsert_reciters(session, [entry("a")])
    await upsert_reciters(session, [entry("a", name_en="Renamed", country="EG", active=False)])
    await session.commit()
    everyone = await load_reciters(session, only_active=False)
    assert [(r.id, r.name_en, r.country, r.active) for r in everyone] == [
        ("a", "Renamed", "EG", False)
    ]
    assert await load_reciters(session) == []
    assert everyone[0].sources["everyayah"][0]["folder"] == "a_64kbps"


async def test_adding_one_reciter_leaves_the_others_untouched(session: AsyncSession) -> None:
    await upsert_reciters(session, [entry("a"), entry("b")])
    await save_gallery(session, gallery_of({A: 4, B: 5}))
    await session.commit()
    before = (
        (await session.execute(select(GalleryClip.id).where(GalleryClip.reciter_id == "a")))
        .scalars()
        .all()
    )

    await save_gallery(session, gallery_of({B: 7}, seed=9), reciter_ids={"b"})
    await session.commit()

    after = (
        (await session.execute(select(GalleryClip.id).where(GalleryClip.reciter_id == "a")))
        .scalars()
        .all()
    )
    assert after == before
    count_b = await session.scalar(
        select(func.count()).select_from(GalleryClip).where(GalleryClip.reciter_id == "b")
    )
    assert count_b == 7


async def test_inactive_reciters_are_not_loaded(session: AsyncSession) -> None:
    await upsert_reciters(session, [entry("a"), entry("b", active=False)])
    await save_gallery(session, gallery_of({A: 3, B: 3}))
    await session.commit()
    assert (await load_gallery(session)).voices == [A]


async def test_deleting_a_reciter_removes_their_embeddings(session: AsyncSession) -> None:
    await upsert_reciters(session, [entry("a")])
    await save_gallery(session, gallery_of({A: 3}))
    await session.commit()
    await session.delete(await session.get_one(Reciter, "a"))
    await session.commit()
    assert await session.scalar(select(func.count()).select_from(GalleryClip)) == 0
    assert await session.scalar(select(func.count()).select_from(ReciterCentroid)) == 0
    assert (await load_gallery(session)).voices == []


async def test_wrong_dimension_is_rejected_by_the_database(session: AsyncSession) -> None:
    from sqlalchemy.exc import DBAPIError

    await upsert_reciters(session, [entry("a")])
    session.add(GalleryClip(reciter_id="a", style="murattal", embedding=[0.1] * 10))
    with pytest.raises(DBAPIError):
        await session.flush()


def test_migrations_upgrade_and_downgrade(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Alembic migration creates and removes the tables the models declare."""
    import asyncio

    url = _require_database()
    monkeypatch.setenv("DATABASE_URL", url)
    ours = {"reciters", "gallery_clips", "reciter_centroids"}

    async def tables(*, reset: bool = False) -> set[str]:
        engine = create_async_engine(url)  # one engine per event loop
        try:
            if reset:
                await _reset(engine)
            async with engine.connect() as conn:
                rows = await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                )
                return {row[0] for row in rows}
        finally:
            await engine.dispose()

    assert not (ours & asyncio.run(tables(reset=True)))
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    assert ours <= asyncio.run(tables())
    command.downgrade(config, "base")
    assert not (ours & asyncio.run(tables()))
    asyncio.run(tables(reset=True))
