"""Reciter registry: names, styles and audio links. No photos, by design."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_index, get_services
from app.api.errors import ApiError
from app.api.schemas import (
    AyahAudioOut,
    ErrorOut,
    ReciterDetailOut,
    ReciterListOut,
    ReciterSummaryOut,
)
from app.matcher.index import QuranIndex
from app.services import ReciterInfo, Services

router = APIRouter(prefix="/v1", tags=["reciters"])

# Per-ayah recordings. Pattern verified in Phase 2 (docs/DATA_SOURCES.md).
EVERYAYAH = "https://everyayah.com/data/{folder}/{sss}{aaa}.mp3"


def _summary(info: ReciterInfo) -> ReciterSummaryOut:
    return ReciterSummaryOut(
        id=info.id,
        name_ar=info.name_ar,
        name_en=info.name_en,
        country=info.country,
        styles=list(info.styles),
    )


@router.get("/reciters", response_model=ReciterListOut)
async def list_reciters(services: Annotated[Services, Depends(get_services)]) -> ReciterListOut:
    ordered = sorted(services.reciters.values(), key=lambda r: r.name_en)
    return ReciterListOut(reciters=[_summary(r) for r in ordered])


@router.get(
    "/reciters/{reciter_id}", response_model=ReciterDetailOut, responses={404: {"model": ErrorOut}}
)
async def get_reciter(
    reciter_id: str,
    services: Annotated[Services, Depends(get_services)],
    index: Annotated[QuranIndex, Depends(get_index)],
    surah: Annotated[int | None, Query(ge=1, le=114)] = None,
    ayah: Annotated[int | None, Query(ge=1)] = None,
) -> ReciterDetailOut:
    """With `surah` and `ayah`, each audio entry also carries the ready-made URL
    for that ayah ("continue listening from this ayah")."""
    info = services.reciters.get(reciter_id)
    if info is None:
        raise ApiError(404, "not_found", "No such reciter.")
    if (surah is None) != (ayah is None):
        raise ApiError(422, "invalid_request", "Give both surah and ayah, or neither.")
    if surah is not None and ayah is not None and ayah > index.surahs[surah - 1].ayah_count:
        raise ApiError(404, "not_found", f"Surah {surah} has no ayah {ayah}.")

    audio = []
    for source in info.sources.get("everyayah", []):
        template = EVERYAYAH.replace("{folder}", source["folder"])
        url = (
            template.replace("{sss}", f"{surah:03d}").replace("{aaa}", f"{ayah:03d}")
            if surah is not None and ayah is not None
            else None
        )
        audio.append(AyahAudioOut(style=source["style"], url_template=template, url=url))
    return ReciterDetailOut(**_summary(info).model_dump(), ayah_audio=audio)
