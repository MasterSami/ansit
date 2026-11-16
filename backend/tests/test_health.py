import asyncio

import httpx

from app.core.readiness import StartupTask
from tests.conftest import make_settings, running_client


async def wait_until_ready(client: httpx.AsyncClient) -> httpx.Response:
    for _ in range(200):
        response = await client.get("/readyz")
        if response.status_code == 200:
            return response
        await asyncio.sleep(0.005)
    raise AssertionError("service never became ready")


async def test_healthz(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readyz_ready_with_no_startup_tasks(client: httpx.AsyncClient) -> None:
    response = await wait_until_ready(client)
    assert response.json() == {"status": "ready", "components": {}, "dependencies": {}}


async def test_readyz_is_503_until_models_load() -> None:
    release = asyncio.Event()

    async def load_model() -> None:
        await release.wait()

    async with running_client(startup_tasks=[StartupTask("asr_model", load_model)]) as client:
        await asyncio.sleep(0)  # let the loader start
        pending = await client.get("/readyz")
        assert pending.status_code == 503
        assert pending.json()["status"] == "not_ready"
        assert pending.json()["components"] == {"asr_model": "pending"}
        # Liveness is independent of model loading.
        assert (await client.get("/healthz")).status_code == 200

        release.set()
        ready = await wait_until_ready(client)
        assert ready.json()["components"] == {"asr_model": "ready"}


async def test_readyz_stays_503_when_a_startup_task_fails() -> None:
    async def broken() -> None:
        raise RuntimeError("model file missing")

    async def fine() -> None:
        return None

    tasks = [StartupTask("asr_model", broken), StartupTask("speaker_model", fine)]
    async with running_client(startup_tasks=tasks) as client:
        for _ in range(50):
            response = await client.get("/readyz")
            if response.json()["components"].get("speaker_model") == "ready":
                break
            await asyncio.sleep(0.005)
        assert response.status_code == 503
        assert response.json()["components"] == {"asr_model": "failed", "speaker_model": "ready"}


async def test_readyz_is_503_when_a_configured_store_is_unreachable() -> None:
    # Port 1 is never listening; the checks must fail fast, not hang.
    settings = make_settings(
        database_url="postgresql+asyncpg://u:p@127.0.0.1:1/db",
        redis_url="redis://127.0.0.1:1/0",
    )
    async with running_client(settings) as client:
        response = await client.get("/readyz")
        assert response.status_code == 503
        assert response.json()["dependencies"] == {"database": False, "redis": False}
