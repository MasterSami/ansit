"""Quran metadata: surahs and ayahs with their neighbours."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import get_index
from app.api.errors import ApiError
from app.api.schemas import (
    AyahContextOut,
    AyahDetailOut,
    AyahTextOut,
    ErrorOut,
    SurahDetailOut,
    SurahListOut,
    SurahOut,
)
from app.identify_service import ayah_out
from app.matcher.index import IndexedAyah, QuranIndex

router = APIRouter(prefix="/v1", tags=["quran"])
NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}}


def _surah(index: QuranIndex, number: int) -> SurahOut:
    surah = index.surahs[number - 1]
    return SurahOut(
        number=surah.number,
        name_ar=surah.name_ar,
        name_en=surah.name_en,
        ayah_count=surah.ayah_count,
        revelation=surah.revelation,
    )


def _text(ayah: IndexedAyah) -> AyahTextOut:
    return AyahTextOut(
        surah=ayah.surah,
        ayah=ayah.ayah,
        text_uthmani=ayah.text_uthmani,
        juz=ayah.juz,
        page=ayah.page,
    )


@router.get("/surahs", response_model=SurahListOut)
async def list_surahs(index: Annotated[QuranIndex, Depends(get_index)]) -> SurahListOut:
    return SurahListOut(surahs=[_surah(index, s.number) for s in index.surahs])


@router.get("/surahs/{number}", response_model=SurahDetailOut, responses=NOT_FOUND)
async def get_surah(
    index: Annotated[QuranIndex, Depends(get_index)],
    number: Annotated[int, Path(ge=1, le=114)],
) -> SurahDetailOut:
    first = index.ayahs[index.ayah_index(number, 1)]
    return SurahDetailOut(
        **_surah(index, number).model_dump(),
        first_page=first.page,
        first_juz=first.juz,
        basmala_uthmani=first.basmala_uthmani,
    )


@router.get("/ayahs/{surah}/{ayah}", response_model=AyahDetailOut, responses=NOT_FOUND)
async def get_ayah(
    index: Annotated[QuranIndex, Depends(get_index)],
    surah: Annotated[int, Path(ge=1, le=114)],
    ayah: Annotated[int, Path(ge=1)],
    context: Annotated[int, Query(ge=0, le=5, description="Neighbouring ayahs on each side.")] = 0,
) -> AyahDetailOut:
    """An ayah with up to `context` ayahs before and after it, within the same surah."""
    if ayah > index.surahs[surah - 1].ayah_count:
        raise ApiError(404, "not_found", f"Surah {surah} has no ayah {ayah}.")
    position = index.ayah_index(surah, ayah)
    start = index.ayah_index(surah, 1)
    end = start + index.surahs[surah - 1].ayah_count
    return AyahDetailOut(
        ayah=ayah_out(index, position),
        basmala_uthmani=index.ayahs[position].basmala_uthmani,
        context=AyahContextOut(
            before=[_text(a) for a in index.ayahs[max(start, position - context) : position]],
            after=[_text(a) for a in index.ayahs[position + 1 : min(end, position + 1 + context)]],
        ),
    )
