import asyncio
import json
import tempfile
import threading
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest

from app.core.ratelimit import MemoryRateLimiter, RateDecision
from app.speaker.engine import l2_normalize
from tests.api.conftest import Harness, api_client, clip, upload
from tests.audio.helpers import encode, tone
from tests.conftest import make_settings
from tests.speaker.test_gallery import near, unit

URL = "/v1/identify"


# ---------------------------------------------------------------- happy paths


async def test_match_has_the_documented_shape(api: httpx.AsyncClient, harness: Harness) -> None:
    harness.say((67, 1))
    response = await api.post(URL, files=upload(clip()), data={"client": "web"})
    assert response.status_code == 200
    body = response.json()

    uuid.UUID(body["id"])
    assert body["status"] == "match"
    assert body["reason"] is None
    mulk = harness.index.ayahs[harness.index.ayah_index(67, 1)]
    assert body["ayah"] == {
        "surah": 67,
        "surah_name_ar": harness.index.surahs[66].name_ar,
        "surah_name_en": "Al-Mulk",
        "ayah": 1,
        "text_uthmani": mulk.text_uthmani,
        "juz": 29,
        "page": 562,
        "revelation": "meccan",
        "ayah_count": 30,
    }
    assert body["span"] == {
        "start": {"surah": 67, "ayah": 1, "word": 1},
        "end": {"surah": 67, "ayah": 1, "word": len(mulk.words)},
    }
    assert body["text_confidence"] == 1.0
    assert body["candidates"] == []
    assert body["repeated_count"] is None
    assert set(body["timings_ms"]) == {"decode", "vad", "asr", "match", "speaker", "total"}
    assert body["timings_ms"]["total"] > 0
    assert "debug" not in body

    reciter = body["reciter"]
    assert reciter["status"] == "identified"
    assert (reciter["id"], reciter["style"]) == ("husary", "murattal")
    assert reciter["name_ar"] == harness.services.reciters["husary"].name_ar
    assert 0.8 < reciter["similarity"] <= 1.0
    assert len(reciter["alternatives"]) == 2
    assert {alt["id"] for alt in reciter["alternatives"]} == {"minshawi", "alafasy"}
    assert all({"id", "name_ar", "similarity"} <= set(alt) for alt in reciter["alternatives"])


async def test_ambiguous_lists_candidates_with_context(
    api: httpx.AsyncClient, harness: Harness
) -> None:
    harness.say((55, 13))
    body = (await api.post(URL, files=upload(clip()))).json()

    assert body["status"] == "ambiguous"
    assert body["repeated_count"] == 31
    assert len(body["candidates"]) == 5
    first = body["candidates"][0]
    assert (first["surah"], first["ayah"], first["score"]) == (55, 13, 1.0)
    previous = harness.index.ayahs[harness.index.ayah_index(55, 12)]
    assert first["context_before"] == previous.text_uthmani
    assert [c["ayah"] for c in body["candidates"]] == sorted(c["ayah"] for c in body["candidates"])
    assert body["ayah"]["surah"] == 55
    assert body["reciter"]["status"] == "identified"


async def test_no_match_reports_no_ayah_and_no_reciter(
    api: httpx.AsyncClient, harness: Harness
) -> None:
    harness.asr.text = " ".join(harness.index.words[i] for i in range(100, 60_000, 4_700))
    body = (await api.post(URL, files=upload(clip()))).json()
    assert (body["status"], body["reason"]) == ("no_match", "low_confidence")
    assert body["ayah"] is None and body["span"] is None and body["text_confidence"] is None
    assert body["reciter"] is None
    assert body["candidates"] == []


@pytest.mark.parametrize(
    ("seconds", "speech_sec", "reason"),
    [(2.0, 6.0, "too_short"), (8.0, 0.7, "no_speech")],
)
async def test_rejected_before_any_model_runs(
    api: httpx.AsyncClient, harness: Harness, seconds: float, speech_sec: float, reason: str
) -> None:
    harness.say((67, 1))
    harness.vad.speech_sec = speech_sec
    body = (await api.post(URL, files=upload(clip(seconds, "wav", "pcm_s16le")))).json()
    assert (body["status"], body["reason"]) == ("no_match", reason)
    assert harness.asr.calls == 0 and harness.speaker.calls == 0
    assert body["timings_ms"]["asr"] == 0 and body["timings_ms"]["speaker"] == 0


async def test_hallucinated_transcript_is_not_matched(
    api: httpx.AsyncClient, harness: Harness
) -> None:
    harness.say((67, 1))
    harness.asr.no_speech = 0.97
    body = (await api.post(URL, files=upload(clip()))).json()
    assert (body["status"], body["reason"]) == ("no_match", "no_speech")


@pytest.mark.parametrize(
    ("container", "codec"),
    [("webm", "libopus"), ("mp4", "aac"), ("mp3", "libmp3lame"), ("wav", "pcm_s16le")],
)
async def test_accepts_every_client_format(
    api: httpx.AsyncClient, harness: Harness, container: str, codec: str
) -> None:
    harness.say((36, 1), (36, 2))
    response = await api.post(URL, files=upload(clip(6.0, container, codec)))
    assert response.status_code == 200
    assert response.json()["status"] == "match"


# -------------------------------------------------------------------- reciter


async def test_unknown_reciter_is_not_named(api: httpx.AsyncClient, harness: Harness) -> None:
    harness.say((67, 1))
    harness.speaker.embedding = unit(999)  # nobody in the gallery
    reciter = (await api.post(URL, files=upload(clip()))).json()["reciter"]
    assert reciter["status"] == "unknown"
    assert reciter["id"] is None and reciter["name_ar"] is None and reciter["style"] is None
    assert reciter["similarity"] < 0.5
    assert 1 <= len(reciter["alternatives"]) <= 2  # offered as "may also be", not asserted


async def test_mujawwad_voice_is_reported_with_its_style(
    api: httpx.AsyncClient, harness: Harness
) -> None:
    harness.say((67, 1))
    harness.speaker.embedding = near(unit(12), seed=3)
    reciter = (await api.post(URL, files=upload(clip()))).json()["reciter"]
    assert (reciter["id"], reciter["style"]) == ("husary", "mujawwad")
    assert "husary" not in {alt["id"] for alt in reciter["alternatives"]}  # one entry per reciter


async def test_close_runner_up_makes_the_reciter_unknown(
    api: httpx.AsyncClient, harness: Harness
) -> None:
    harness.say((67, 1))
    harness.speaker.embedding = l2_normalize(unit(13) + unit(14))  # between two reciters
    reciter = (await api.post(URL, files=upload(clip()))).json()["reciter"]
    assert reciter["status"] == "unknown"
    assert {alt["id"] for alt in reciter["alternatives"]} == {"minshawi", "alafasy"}


async def test_without_a_gallery_the_reciter_is_unknown(harness: Harness) -> None:
    harness.say((67, 1))
    harness.services.speaker = None
    harness.services.gallery = None
    async with api_client(harness) as client:
        body = (await client.post(URL, files=upload(clip()))).json()
    assert body["status"] == "match"
    assert body["reciter"] == {
        "status": "unknown",
        "id": None,
        "name_ar": None,
        "name_en": None,
        "style": None,
        "similarity": None,
        "alternatives": [],
    }


# ------------------------------------------------------------ both branches


async def test_ayah_and_reciter_branches_run_at_the_same_time(
    api: httpx.AsyncClient, harness: Harness
) -> None:
    """The ASR call only returns once the speaker call has started, which can
    only happen if the two run in different threads concurrently."""
    harness.say((67, 1))
    harness.asr.gate = harness.speaker.signal = threading.Event()
    response = await asyncio.wait_for(api.post(URL, files=upload(clip())), timeout=4)
    assert response.json()["status"] == "match"
    assert harness.asr.threads[0] != harness.speaker.threads[0]


async def test_busy_server_answers_503_instead_of_queueing_forever(harness: Harness) -> None:
    harness.say((67, 1))
    harness.asr.gate = threading.Event()
    settings = make_settings(
        rate_limit_per_min=1000, max_concurrent_identify=1, identify_queue_timeout_sec=0.1
    )
    async with api_client(harness, settings) as client:
        first = asyncio.create_task(client.post(URL, files=upload(clip())))
        await asyncio.sleep(0.3)  # the first request now holds the only slot
        second = await client.post(URL, files=upload(clip()))
        assert second.status_code == 503
        assert second.json()["error"]["code"] == "server_busy"
        assert second.headers["retry-after"] == "2"
        harness.asr.gate.set()
        assert (await first).status_code == 200


async def test_not_ready_while_models_are_loading() -> None:
    async with api_client(None) as client:
        response = await client.post(URL, files=upload(clip()))
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "not_ready"


# --------------------------------------------------------------------- debug


async def test_debug_needs_both_the_request_flag_and_the_server_switch(harness: Harness) -> None:
    harness.say((67, 1))
    async with api_client(harness) as client:  # ALLOW_DEBUG is off by default
        body = (await client.post(URL, files=upload(clip()), data={"debug": "true"})).json()
        assert "debug" not in body

    settings = make_settings(rate_limit_per_min=1000, allow_debug=True)
    async with api_client(harness, settings) as client:
        quiet = (await client.post(URL, files=upload(clip()))).json()
        assert "debug" not in quiet
        harness.asr.text = harness.ayah_text(1, 1) + " " + harness.ayah_text(67, 1)
        body = (await client.post(URL, files=upload(clip()), data={"debug": "true"})).json()
        assert body["debug"] == {
            "transcript_normalized": harness.asr.text,
            "prefix_detected": "basmala",
        }


# -------------------------------------------------------------------- limits


async def test_unreadable_audio(api: httpx.AsyncClient) -> None:
    response = await api.post(URL, files=upload(b"this is not audio"))
    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "audio_unreadable", "message": "The audio could not be decoded."}
    }


async def test_clip_longer_than_the_maximum(api: httpx.AsyncClient, harness: Harness) -> None:
    harness.say((67, 1))
    response = await api.post(URL, files=upload(clip(16.5, "mp3", "libmp3lame")))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "audio_too_long"
    assert harness.asr.calls == 0


async def test_upload_over_the_size_limit(harness: Harness) -> None:
    settings = make_settings(rate_limit_per_min=1000, max_upload_mb=0.25)
    wav = clip(9.0, "wav", "pcm_s16le")  # 288 kB: over the limit, inside the body cap
    huge = encode(tone(14.0, rate=48_000), "wav", "pcm_s16le", source_rate=48_000, channels=2)
    async with api_client(harness, settings) as client:
        over = await client.post(URL, files=upload(wav))
        assert over.status_code == 413
        assert over.json()["error"]["code"] == "audio_too_large"
        # Far over: refused from Content-Length, before the body is read at all.
        refused = await client.post(URL, files=upload(huge))
        assert refused.status_code == 413
        assert refused.json()["error"]["code"] == "payload_too_large"
    assert harness.asr.calls == 0


async def test_body_cap_also_applies_without_a_content_length(harness: Harness) -> None:
    settings = make_settings(rate_limit_per_min=1000, max_upload_mb=0.25)

    async def chunks() -> AsyncIterator[bytes]:
        yield b'--x\r\nContent-Disposition: form-data; name="audio"; filename="a.wav"\r\n\r\n'
        for _ in range(64):
            yield b"x" * 16_384

    async with api_client(harness, settings) as client:
        response = await client.post(
            URL, content=chunks(), headers={"content-type": "multipart/form-data; boundary=x"}
        )
    assert response.status_code == 413


async def test_request_validation_errors_use_the_error_shape(api: httpx.AsyncClient) -> None:
    missing = await api.post(URL, data={"client": "web"})
    assert missing.status_code == 422
    assert missing.json()["error"]["code"] == "invalid_request"
    assert "audio" in missing.json()["error"]["message"]

    bad_client = await api.post(URL, files=upload(clip()), data={"client": "smart-fridge"})
    assert bad_client.status_code == 422
    assert bad_client.json()["error"]["code"] == "invalid_request"

    bad_previous = await api.post(URL, files=upload(clip()), data={"previous_identify_id": "nope"})
    assert bad_previous.status_code == 422


async def test_unknown_routes_use_the_error_shape(api: httpx.AsyncClient) -> None:
    response = await api.get("/v1/nothing-here")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert (await api.get(URL)).json()["error"]["code"] == "method_not_allowed"


# -------------------------------------------------------------- rate limiting


async def test_rate_limit_per_ip(harness: Harness) -> None:
    harness.say((67, 1))
    settings = make_settings(rate_limit_per_min=2)
    async with api_client(harness, settings) as client:
        assert (await client.post(URL, files=upload(clip()))).status_code == 200
        assert (await client.post(URL, files=upload(clip()))).status_code == 200
        limited = await client.post(URL, files=upload(clip()))
        assert limited.status_code == 429
        assert limited.json()["error"]["code"] == "rate_limited"
        assert 1 <= int(limited.headers["retry-after"]) <= 60
        # read-only endpoints are not limited
        assert (await client.get("/v1/surahs")).status_code == 200
    assert harness.asr.calls == 2


async def test_rate_limit_per_device(harness: Harness) -> None:
    """Two devices behind one IP are counted separately as devices."""
    harness.say((67, 1))

    class DeviceOnly:
        def __init__(self) -> None:
            self.inner = MemoryRateLimiter(limit=1)
            self.keys: list[str] = []

        async def hit(self, key: str) -> RateDecision:
            self.keys.append(key)
            return await self.inner.hit(key) if key.startswith("device:") else RateDecision(True, 1)

    limiter = DeviceOnly()
    async with api_client(harness, limiter=limiter) as client:
        a = {"X-Device-ID": "device-aaaa-1111"}
        b = {"X-Device-ID": "device-bbbb-2222"}
        assert (await client.post(URL, files=upload(clip()), headers=a)).status_code == 200
        assert (await client.post(URL, files=upload(clip()), headers=a)).status_code == 429
        assert (await client.post(URL, files=upload(clip()), headers=b)).status_code == 200
        # a malformed id is ignored rather than trusted
        bad = {"X-Device-ID": "x y"}
        assert (await client.post(URL, files=upload(clip()), headers=bad)).status_code == 200
    assert "device:device-aaaa-1111" in limiter.keys
    assert not any("x y" in key for key in limiter.keys)


async def test_forwarded_for_is_ignored_unless_proxies_are_trusted(harness: Harness) -> None:
    harness.say((67, 1))
    spoof = [{"X-Forwarded-For": f"10.0.0.{i}"} for i in range(3)]
    async with api_client(harness, make_settings(rate_limit_per_min=1)) as client:
        codes = [
            (await client.post(URL, files=upload(clip()), headers=h)).status_code for h in spoof
        ]
    assert codes == [200, 429, 429]  # same socket peer, whatever the header claims

    trusting = make_settings(rate_limit_per_min=1, trust_proxy_headers=True)
    async with api_client(harness, trusting) as client:
        codes = [
            (await client.post(URL, files=upload(clip()), headers=h)).status_code for h in spoof
        ]
    assert codes == [200, 200, 200]


# ------------------------------------------------------------ listen longer


def _repeated_pair(harness: Harness) -> tuple[int, int]:
    """Positions (a, b): the 4 words at `a` and the 4 words at `b` (shortly
    after) each occur several times in the Quran, but only here in this order."""
    index = harness.index
    for a in range(0, len(index.words) - 16):
        first = index.occurrences(a, a + 3)
        if not 2 <= len(first) <= 6:
            continue
        b = a + 6
        second = index.occurrences(b, b + 3)
        if not 2 <= len(second) <= 6:
            continue
        follows = [s for s in second if any(-3 <= s - (f + 3) <= 80 for f in first)]
        if follows == [b]:
            return a, b
    raise AssertionError("no such pair in the index")


async def test_listen_longer_resolves_an_ambiguous_result(
    api: httpx.AsyncClient, harness: Harness
) -> None:
    a, b = _repeated_pair(harness)
    words = harness.index.words

    harness.asr.text = " ".join(words[a : a + 4])
    first = (await api.post(URL, files=upload(clip()))).json()
    assert first["status"] == "ambiguous"

    harness.asr.text = " ".join(words[b : b + 4])
    alone = (await api.post(URL, files=upload(clip()))).json()
    assert alone["status"] == "ambiguous"  # on its own the second clip is ambiguous too

    resolved = (
        await api.post(URL, files=upload(clip()), data={"previous_identify_id": first["id"]})
    ).json()
    assert resolved["status"] == "match"
    assert resolved["candidates"] == [] and resolved["repeated_count"] is None
    expected = harness.index.word_ref(b)
    assert resolved["span"]["start"] == {
        "surah": expected.surah,
        "ayah": expected.ayah,
        "word": expected.word,
    }


async def test_unknown_previous_id_changes_nothing(
    api: httpx.AsyncClient, harness: Harness
) -> None:
    harness.say((55, 13))
    body = (
        await api.post(URL, files=upload(clip()), data={"previous_identify_id": str(uuid.uuid4())})
    ).json()
    assert body["status"] == "ambiguous" and body["repeated_count"] == 31


# -------------------------------------------------------------------- privacy


async def test_the_clip_never_reaches_the_disk(
    harness: Harness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing is written, and the upload is never spooled to a temp file,
    including for an upload larger than the framework's 1 MB in-memory default."""
    harness.say((67, 1))
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    spilled: list[str] = []
    original = tempfile.SpooledTemporaryFile.rollover

    def recording_rollover(self: tempfile.SpooledTemporaryFile[bytes]) -> None:
        spilled.append("rollover")
        original(self)

    monkeypatch.setattr(tempfile.SpooledTemporaryFile, "rollover", recording_rollover)

    big = encode(tone(9.0, rate=48_000), "wav", "pcm_s16le", source_rate=48_000, channels=2)
    assert 1_500_000 < len(big) < 2 * 1024 * 1024
    async with api_client(harness) as client:
        response = await client.post(URL, files=upload(big, "clip.wav"))
    assert response.json()["status"] == "match"
    assert spilled == []
    assert list(tmp_path.iterdir()) == []  # noqa: ASYNC240 - a test, after the request


async def test_logs_contain_neither_audio_nor_transcript(
    harness: Harness, capsys: pytest.CaptureFixture[str]
) -> None:
    harness.say((67, 1))
    settings = make_settings(rate_limit_per_min=1000, log_level="INFO", allow_debug=True)
    async with api_client(harness, settings) as client:
        await client.post(URL, files=upload(clip()), data={"debug": "true", "client": "ios"})
    output = capsys.readouterr().out

    events = [json.loads(line) for line in output.splitlines() if line.startswith("{")]
    identify = next(e for e in events if e["event"] == "identify")
    assert identify["status"] == "match" and identify["client"] == "ios"
    assert set(identify) <= {
        "event", "level", "logger", "timestamp", "request_id", "identify_id", "status",
        "reason", "reciter_status", "clip_sec", "total_ms", "client",
    }  # fmt: skip
    for word in harness.asr.text.split():
        assert word not in output
    assert "transcript" not in output


# -------------------------------------------------------------------- metrics


async def test_metrics_record_outcomes_stages_and_confidence(
    api: httpx.AsyncClient, harness: Harness
) -> None:
    harness.say((67, 1))
    await api.post(URL, files=upload(clip()), data={"client": "android"})
    await api.post(URL, files=upload(b"junk"))
    text = (await api.get("/metrics")).text

    assert 'ansit_identify_total{client="android",reason="",status="match"}' in text
    for stage in ("decode", "vad", "asr", "match", "speaker", "total"):
        assert f'ansit_identify_stage_duration_seconds_count{{stage="{stage}"}}' in text
    assert "ansit_text_confidence_bucket" in text
    assert 'ansit_reciter_similarity_bucket{le="1.0",status="identified"}' in text
    assert 'ansit_reciter_total{status="identified"}' in text
    assert 'ansit_identify_rejected_total{code="audio_unreadable"}' in text
    assert "ansit_identify_in_flight 0.0" in text
    assert 'route="/v1/identify"' in text
