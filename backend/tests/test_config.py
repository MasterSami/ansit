import pytest
from pydantic import ValidationError

from app.core.config import Settings
from tests.conftest import make_settings


def test_defaults_match_the_brief() -> None:
    settings = make_settings()
    assert settings.min_speech_sec == 1.5
    assert settings.min_clip_sec == 3
    assert settings.max_clip_sec == 15
    assert settings.max_upload_mb == 2
    assert settings.asr_device == "cpu"
    assert settings.asr_compute_type == "int8"
    assert settings.allow_debug is False
    assert settings.cors_origins == []
    assert settings.database_url is None
    assert (settings.reciter_threshold, settings.reciter_min_margin) == (0.60, 0.08)
    assert settings.gallery_path is None
    assert settings.redis_url is None


def test_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://a.example, https://b.example ,")
    monkeypatch.setenv("ALLOW_DEBUG", "true")
    monkeypatch.setenv("MAX_UPLOAD_MB", "1.5")
    monkeypatch.setenv("REDIS_URL", "")
    settings = Settings(_env_file=None)
    assert settings.cors_origins == ["https://a.example", "https://b.example"]
    assert settings.allow_debug is True
    assert settings.max_upload_mb == 1.5
    assert settings.redis_url is None


def test_invalid_values_fail_loudly() -> None:
    with pytest.raises(ValidationError):
        make_settings(asr_device="tpu")
    with pytest.raises(ValidationError):
        make_settings(asr_beam_size=0)


async def test_cors_allowlist_is_enforced() -> None:
    from tests.conftest import running_client

    settings = make_settings(cors_origins=["https://ansit.example"])
    async with running_client(settings) as client:
        allowed = await client.get("/healthz", headers={"Origin": "https://ansit.example"})
        assert allowed.headers["access-control-allow-origin"] == "https://ansit.example"
        denied = await client.get("/healthz", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in denied.headers
