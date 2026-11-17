"""End-to-end through HTTP with the real models. Runs only where the artifacts
and the evaluation clips have been built locally; skipped everywhere else."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from asgi_lifespan import LifespanManager

from app.main import create_app
from tests.conftest import make_settings

REPO = Path(__file__).resolve().parents[3]
ARTIFACTS = REPO / "ml" / "artifacts"
MANIFEST = REPO / "ml" / "data" / "eval_audio" / "manifest.jsonl"
NEEDED = [
    ARTIFACTS / "quran_index.json.gz",
    ARTIFACTS / "asr" / "tarteel-base" / "model.bin",
    ARTIFACTS / "speaker" / "resnet34.onnx",
    ARTIFACTS / "gallery.npz",
    MANIFEST,
]


async def test_real_clip_is_identified_with_its_reciter() -> None:
    if not all(path.is_file() for path in NEEDED):
        pytest.skip("models, gallery or evaluation clips not built locally")
    rows = [json.loads(line) for line in MANIFEST.read_text().splitlines()]
    row = next(
        r
        for r in rows
        if r["reciter"] == "Alafasy_64kbps" and r["condition"] == "phone" and r["duration"] == 12.0
    )
    data = (MANIFEST.parent / row["path"]).read_bytes()

    settings = make_settings(load_models=True, rate_limit_per_min=1000)
    async with LifespanManager(create_app(settings), startup_timeout=120) as manager:
        transport = httpx.ASGITransport(app=manager.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(300):  # models load in the background
                if (await client.get("/readyz")).status_code == 200:
                    break
                await asyncio.sleep(0.2)
            ready = (await client.get("/readyz")).json()
            assert ready["components"] == {
                "quran_index": "ready",
                "asr_model": "ready",
                "speaker_model": "ready",
                "reciter_gallery": "ready",
            }
            response = await client.post(
                "/v1/identify", files={"audio": ("clip.webm", data, "audio/webm")}
            )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] in ("match", "ambiguous")
    assert f"{body['ayah']['surah']}:{body['ayah']['ayah']}" in row["overlaps"]
    assert body["reciter"]["status"] == "identified"
    assert body["reciter"]["id"] == "alafasy"
    assert body["timings_ms"]["asr"] > 0 and body["timings_ms"]["speaker"] > 0
