"""API behaviour that needs PostgreSQL: identify events, feedback, gallery loading.

Uses the same TEST_DATABASE_URL convention as test_store.py.
"""

import json
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base, Feedback, IdentifyEvent
from app.services import Services, build_startup_tasks
from app.speaker.store import save_gallery, upsert_reciters
from tests.api.conftest import Harness, api_client, clip, harness, upload
from tests.conftest import make_settings
from tests.db.test_store import _require_database, _reset, entry

__all__ = ["harness"]  # the API harness fixture, reused here


@pytest.fixture
async def database_url() -> AsyncIterator[str]:
    url = _require_database()
    engine = create_async_engine(url)
    await _reset(engine)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    yield url
    await _reset(engine)
    await engine.dispose()


async def rows(url: str, model: type[Any]) -> list[Any]:
    engine = create_async_engine(url)
    async with AsyncSession(engine) as session:
        found = list((await session.execute(select(model))).scalars())
    await engine.dispose()
    return found


async def test_identify_event_is_stored_without_audio_or_transcript(
    harness: Harness, database_url: str
) -> None:
    harness.say((67, 1))
    settings = make_settings(rate_limit_per_min=1000, database_url=database_url)
    async with api_client(harness, settings) as client:
        body = (
            await client.post(
                "/v1/identify",
                files=upload(clip()),
                data={"client": "ios"},
                headers={"X-App-Version": "1.2.3"},
            )
        ).json()
        await client.post("/v1/identify", files=upload(clip(2.0, "wav", "pcm_s16le")))
    # leaving the context drains pending event writes

    events = {e.status: e for e in await rows(database_url, IdentifyEvent)}
    assert set(events) == {"match", "no_match"}
    match = events["match"]
    assert str(match.id) == body["id"]
    assert (match.client, match.app_version) == ("ios", "1.2.3")
    assert match.text_confidence == 1.0
    assert (match.reciter_status, match.reciter_id) == ("identified", "husary")
    assert 7.5 < match.clip_sec < 8.5
    assert set(match.timings_ms) == {"decode", "vad", "asr", "match", "speaker", "total"}
    assert events["no_match"].reason == "too_short"
    assert events["no_match"].reciter_status is None

    # The table has no place to put a transcript or audio, and no row holds one.
    engine = create_async_engine(database_url)
    async with engine.connect() as conn:
        columns = await conn.run_sync(
            lambda sync: {c["name"] for c in inspect(sync).get_columns("identify_events")}
        )
        dump = (
            await conn.execute(text("SELECT row_to_json(e)::text FROM identify_events e"))
        ).all()
    await engine.dispose()
    assert not {c for c in columns if "transcript" in c or "audio" in c or c == "text"}
    for word in harness.asr.text.split():
        assert all(word not in row[0] for row in dump)


async def test_feedback_is_stored(harness: Harness, database_url: str) -> None:
    settings = make_settings(rate_limit_per_min=1000, database_url=database_url)
    identify_id = str(uuid.uuid4())
    async with api_client(harness, settings) as client:
        response = await client.post(
            "/v1/feedback",
            json={
                "identify_id": identify_id,
                "kind": "wrong_reciter",
                "correct_reciter_id": "minshawi",
            },
        )
        assert response.status_code == 201
        assert response.json() == {"stored": True}
        second = await client.post(
            "/v1/feedback",
            json={
                "identify_id": identify_id,
                "kind": "wrong_ayah",
                "correct_surah": 67,
                "correct_ayah": 2,
            },
        )
        assert second.status_code == 201

    stored = sorted(await rows(database_url, Feedback), key=lambda f: f.id)
    assert [(f.kind, f.correct_reciter_id, f.correct_surah, f.correct_ayah) for f in stored] == [
        ("wrong_reciter", "minshawi", None, None),
        ("wrong_ayah", None, 67, 2),
    ]
    assert all(str(f.identify_id) == identify_id for f in stored)
    assert all(f.created_at is not None for f in stored)


async def test_feedback_is_rate_limited(harness: Harness, database_url: str) -> None:
    settings = make_settings(rate_limit_per_min=1, database_url=database_url)
    payload = {"identify_id": str(uuid.uuid4()), "kind": "other"}
    async with api_client(harness, settings) as client:
        assert (await client.post("/v1/feedback", json=payload)).status_code == 201
        assert (await client.post("/v1/feedback", json=payload)).status_code == 429


# ----------------------------------------------------- gallery loading at start


async def run_gallery_task(settings_kwargs: dict[str, object], url: str | None) -> Services:
    settings = make_settings(load_models=True, database_url=url, **settings_kwargs)
    services = Services()
    sessions = None
    engine = None
    if url is not None:
        engine = create_async_engine(url)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
    task = next(
        t for t in build_startup_tasks(settings, services, sessions) if t.name == "reciter_gallery"
    )
    try:
        await task.run()
    finally:
        if engine is not None:
            await engine.dispose()
    return services


def write_files(harness: Harness, tmp_path: Path) -> dict[str, object]:
    gallery = harness.services.gallery
    assert gallery is not None
    gallery.save(tmp_path / "gallery.npz")
    registry = [entry(r, styles=list(info.styles)) for r, info in harness.services.reciters.items()]
    (tmp_path / "reciters.json").write_text(json.dumps(registry), encoding="utf-8")
    return {
        "gallery_path": str(tmp_path / "gallery.npz"),
        "registry_path": str(tmp_path / "reciters.json"),
    }


async def test_gallery_comes_from_the_database_when_it_has_one(
    harness: Harness, database_url: str, tmp_path: Path
) -> None:
    gallery = harness.services.gallery
    assert gallery is not None
    engine = create_async_engine(database_url)
    async with AsyncSession(engine) as session:
        await upsert_reciters(
            session,
            [entry(r, name_en=f"From DB {r}") for r in harness.services.reciters],
        )
        await save_gallery(session, gallery)
        await session.commit()
    await engine.dispose()

    loaded = await run_gallery_task(write_files(harness, tmp_path), database_url)
    assert loaded.gallery is not None
    assert len(loaded.gallery.embeddings) == len(gallery.embeddings)
    assert loaded.reciters["husary"].name_en == "From DB husary"  # not the file's


async def test_gallery_falls_back_to_files_when_the_database_is_empty(
    harness: Harness, database_url: str, tmp_path: Path
) -> None:
    loaded = await run_gallery_task(write_files(harness, tmp_path), database_url)
    assert loaded.gallery is not None
    assert {v.reciter_id for v in loaded.gallery.voices} == set(loaded.reciters)
    assert loaded.reciters["husary"].name_en == "Name husary"


async def test_gallery_from_files_without_any_database(harness: Harness, tmp_path: Path) -> None:
    loaded = await run_gallery_task(write_files(harness, tmp_path), None)
    assert loaded.gallery is not None and len(loaded.reciters) == 3


async def test_no_gallery_anywhere_fails_the_startup_task(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="no reciter gallery"):
        await run_gallery_task({"gallery_path": None, "registry_path": None}, None)


async def test_gallery_with_reciters_missing_from_the_registry_is_refused(
    harness: Harness, tmp_path: Path
) -> None:
    paths = write_files(harness, tmp_path)
    registry = Path(str(paths["registry_path"]))
    registry.write_text(  # noqa: ASYNC240 - test setup
        json.dumps([entry("husary", styles=["murattal", "mujawwad"])]), encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="missing from the registry"):
        await run_gallery_task(paths, None)
