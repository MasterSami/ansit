import os
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
from asgi_lifespan import LifespanManager

from app.core.config import Settings
from app.core.readiness import StartupTask
from app.main import create_app
from app.matcher.index import QuranIndex
from app.matcher.normalize import DEFAULT_CONFIG
from app.matcher.quran_data import SIMPLE_FILE, QuranData, load_quran
from app.matcher.search import AyahMatcher


def make_settings(**overrides: object) -> Settings:
    """Settings isolated from the developer's `.env` and process environment."""
    options: dict[str, object] = {"app_env": "test", "load_models": False, **overrides}
    return Settings(_env_file=None, **options)  # type: ignore[arg-type]


@asynccontextmanager
async def running_client(
    settings: Settings | None = None,
    startup_tasks: Sequence[StartupTask] | None = None,
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(settings or make_settings(), startup_tasks)
    async with LifespanManager(app) as manager:
        transport = httpx.ASGITransport(app=manager.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    async with running_client() as c:
        yield c


# --- real Tanzil data. No Quran text is typed in the tests: ayahs are referred
# --- to by (surah, ayah) and their text is read from the data.

REPO = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("ANSIT_QURAN_DATA_DIR", REPO / "ml" / "data" / "tanzil"))


@pytest.fixture(scope="session")
def data_dir() -> Path:
    if not (DATA_DIR / SIMPLE_FILE).is_file():
        message = f"Tanzil data not found in {DATA_DIR}; run `make data`"
        if os.environ.get("ANSIT_REQUIRE_QURAN_DATA") == "1":
            pytest.fail(message)  # CI must never silently skip these
        pytest.skip(message)
    return DATA_DIR


@pytest.fixture(scope="session")
def quran(data_dir: Path) -> QuranData:
    return load_quran(data_dir)


@pytest.fixture(scope="session")
def index(quran: QuranData) -> QuranIndex:
    return QuranIndex.build(quran, DEFAULT_CONFIG)


@pytest.fixture(scope="session")
def matcher(index: QuranIndex) -> AyahMatcher:
    return AyahMatcher(index, match_threshold=76, ambiguity_delta=2)
