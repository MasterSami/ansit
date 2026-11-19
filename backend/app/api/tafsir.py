"""Per-ayah tafsir, fetched lazily from QuranEnc and cached by coordinate."""

import asyncio
import json
import time
from typing import Annotated, Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, Path, Query, Response

from app.api.deps import get_index
from app.api.errors import ApiError
from app.api.schemas import ErrorOut, TafsirOut
from app.matcher.index import QuranIndex

router = APIRouter(prefix="/v1", tags=["tafsir"])
NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}}

SOURCE_KEY = "arabic_moyassar"
SOURCE_URL = f"https://quranenc.com/ar/browse/{SOURCE_KEY}"
API_ROOT = "https://quranenc.com/api/v1"
CACHE_SECONDS = 6 * 60 * 60
_cache: dict[tuple[str, int, int], tuple[float, TafsirOut]] = {}


def _read_json(url: str) -> dict[str, Any]:
    if not url.startswith(f"{API_ROOT}/"):
        raise ValueError("Tafsir requests must stay on the configured QuranEnc API")
    request = Request(  # noqa: S310 - URL is restricted to the fixed HTTPS API root
        url, headers={"User-Agent": "ANSIT/0.1 (Quran tafsir lookup)"}
    )
    with urlopen(request, timeout=8) as response:  # noqa: S310 - fixed HTTPS host
        body = json.loads(response.read())
    if not isinstance(body, dict):
        raise ValueError("QuranEnc returned an unexpected response")
    return body


async def _fetch_json(url: str) -> dict[str, Any]:
    return await asyncio.to_thread(_read_json, url)


async def _get_tafsir(surah: int, ayah: int) -> TafsirOut:
    key = (SOURCE_KEY, surah, ayah)
    cached = _cache.get(key)
    if cached and cached[0] > time.monotonic():
        return cached[1]

    try:
        ayah_data = await _fetch_json(f"{API_ROOT}/translation/aya/{SOURCE_KEY}/{surah}/{ayah}")
    except (OSError, URLError, TimeoutError, ValueError) as exc:
        raise ApiError(502, "tafsir_unavailable", "The tafsir source is unavailable.") from exc

    row = ayah_data.get("result")
    if isinstance(row, list):
        row = next(
            (
                item
                for item in row
                if isinstance(item, dict)
                and str(item.get("sura")) == str(surah)
                and str(item.get("aya")) == str(ayah)
            ),
            None,
        )
    if isinstance(row, dict) and (
        str(row.get("sura")) != str(surah) or str(row.get("aya")) != str(ayah)
    ):
        row = None
    text = row.get("translation") if isinstance(row, dict) else None
    if not isinstance(text, str) or not text:
        raise ApiError(502, "tafsir_unavailable", "The tafsir source returned incomplete data.")

    result = TafsirOut(
        surah=surah,
        ayah=ayah,
        text=text,
        source_key=SOURCE_KEY,
        book="التفسير الميسر",
        author="نخبة من العلماء",
        publisher="مجمع الملك فهد لطباعة المصحف الشريف",
        version="غير منشور من المصدر",
        source_url=f"{SOURCE_URL}/{surah}/{ayah}",
        attribution=(
            "التفسير الميسر — مجمع الملك فهد؛ المصدر QuranEnc.com. لم يعلن المصدر رقم إصدار."
        ),
    )
    _cache[key] = (time.monotonic() + CACHE_SECONDS, result)
    return result


@router.get("/tafsir/{surah}/{ayah}", response_model=TafsirOut, responses=NOT_FOUND)
async def get_tafsir(
    response: Response,
    index: Annotated[QuranIndex, Depends(get_index)],
    surah: Annotated[int, Path(ge=1, le=114)],
    ayah: Annotated[int, Path(ge=1)],
    source: Annotated[str, Query(description="QuranEnc edition key.")] = SOURCE_KEY,
) -> TafsirOut:
    """Fetch just the requested ayah. Both coordinates follow the local Quran index."""
    if source != SOURCE_KEY:
        raise ApiError(404, "not_found", "No such tafsir source.")
    if ayah > index.surahs[surah - 1].ayah_count:
        raise ApiError(404, "not_found", f"Surah {surah} has no ayah {ayah}.")
    response.headers["Cache-Control"] = (
        f"public, max-age={CACHE_SECONDS}, stale-while-revalidate=86400"
    )
    return await _get_tafsir(surah, ayah)
