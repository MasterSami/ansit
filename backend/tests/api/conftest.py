"""API test harness: the real Quran index with scripted engines and a synthetic
gallery. No model files and no recitation audio are needed."""

import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import httpx
import numpy as np
import pytest
from asgi_lifespan import LifespanManager

from app.asr.engine import ASRResult
from app.audio.decode import Waveform
from app.audio.vad import SpeechActivity
from app.core.config import Settings
from app.core.ratelimit import RateLimiter
from app.main import create_app
from app.matcher.index import QuranIndex
from app.matcher.search import AyahMatcher
from app.pipeline import AyahIdentifier
from app.services import ReciterInfo, Services, audio_limits
from app.speaker.engine import Embedding
from app.speaker.gallery import Gallery, Voice
from tests.audio.helpers import encode, tone
from tests.conftest import make_settings
from tests.speaker.test_gallery import near, unit

VOICES = {
    Voice("husary", "murattal"): unit(11),
    Voice("husary", "mujawwad"): unit(12),
    Voice("minshawi", "murattal"): unit(13),
    Voice("alafasy", "murattal"): unit(14),
}


@dataclass
class FakeASR:
    text: str = ""
    logprob: float = -0.05
    no_speech: float = 0.0
    calls: int = 0
    gate: threading.Event | None = None  # when set, transcribe() blocks until it fires
    threads: list[int] = field(default_factory=list)

    def transcribe(self, waveform_16k: Waveform) -> ASRResult:
        self.calls += 1
        self.threads.append(threading.get_ident())
        if self.gate is not None:
            self.gate.wait(timeout=5)
        return ASRResult(self.text, self.logprob, self.no_speech, 12.0, 1.1)


@dataclass
class FakeVAD:
    speech_sec: float = 6.0

    def detect(self, waveform: Waveform) -> SpeechActivity:
        return SpeechActivity(self.speech_sec, 0, len(waveform))


@dataclass
class FakeSpeaker:
    embedding: Embedding = field(default_factory=lambda: near(unit(11), seed=1))
    calls: int = 0
    threads: list[int] = field(default_factory=list)
    signal: threading.Event | None = None  # fired when embed() starts

    def embed(self, waveform_16k: Waveform) -> Embedding:
        self.calls += 1
        self.threads.append(threading.get_ident())
        if self.signal is not None:
            self.signal.set()
        return self.embedding


@dataclass
class Harness:
    services: Services
    asr: FakeASR
    vad: FakeVAD
    speaker: FakeSpeaker
    index: QuranIndex

    def ayah_text(self, surah: int, ayah: int) -> str:
        return " ".join(self.index.ayahs[self.index.ayah_index(surah, ayah)].words)

    def say(self, *refs: tuple[int, int]) -> None:
        """Make the ASR "hear" these ayahs."""
        self.asr.text = " ".join(self.ayah_text(s, a) for s, a in refs)


def reciter_info(reciter_id: str, styles: tuple[str, ...]) -> ReciterInfo:
    return ReciterInfo(
        id=reciter_id,
        name_ar=f"اسم {reciter_id}",
        name_en=f"Name {reciter_id}",
        country=None,
        styles=styles,
        sources={"everyayah": [{"folder": f"{reciter_id}_{s}_64kbps", "style": s} for s in styles]},
    )


@pytest.fixture
def harness(index: QuranIndex, matcher: AyahMatcher) -> Harness:
    asr, vad, speaker = FakeASR(), FakeVAD(), FakeSpeaker()
    settings = make_settings()
    vectors, owners = [], []
    for number, centre in enumerate(VOICES.values()):
        for clip in range(8):
            vectors.append(near(centre, seed=100 * number + clip))
            owners.append(number)
    gallery = Gallery(list(VOICES), np.stack(vectors), np.asarray(owners, dtype=np.intp))
    services = Services(
        index=index,
        identifier=AyahIdentifier(asr, matcher, vad, audio_limits(settings)),  # type: ignore[arg-type]
        speaker=speaker,
        gallery=gallery,
        reciters={
            "husary": reciter_info("husary", ("murattal", "mujawwad")),
            "minshawi": reciter_info("minshawi", ("murattal",)),
            "alafasy": reciter_info("alafasy", ("murattal",)),
        },
    )
    return Harness(services, asr, vad, speaker, index)


@asynccontextmanager
async def api_client(
    harness: Harness | None,
    settings: Settings | None = None,
    limiter: RateLimiter | None = None,
) -> AsyncIterator[httpx.AsyncClient]:
    settings = settings or make_settings(rate_limit_per_min=1000)
    app = create_app(settings, services=harness.services if harness else None, limiter=limiter)
    if harness is not None:
        # The identifier was built with default limits; follow the test's settings.
        assert harness.services.identifier is not None
        harness.services.identifier.limits = audio_limits(settings)
    async with LifespanManager(app) as manager:
        transport = httpx.ASGITransport(app=manager.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            client.app = app  # type: ignore[attr-defined]
            yield client


@pytest.fixture
async def api(harness: Harness) -> AsyncIterator[httpx.AsyncClient]:
    async with api_client(harness) as client:
        yield client


def clip(seconds: float = 8.0, container: str = "webm", codec: str = "libopus") -> bytes:
    """A synthetic upload. The fake engines decide what it "contains"."""
    return encode(tone(seconds), container, codec)


def upload(data: bytes, name: str = "clip.webm") -> dict[str, tuple[str, bytes, str]]:
    return {"audio": (name, data, "application/octet-stream")}
