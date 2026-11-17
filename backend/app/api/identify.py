"""POST /v1/identify."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

from app.api.deps import app_version, enforce_rate_limit, get_identify_service, get_settings
from app.api.errors import ApiError
from app.api.schemas import Client, ErrorOut, IdentifyResponse
from app.core.config import Settings
from app.core.metrics import IDENTIFY_REJECTED
from app.identify_service import IdentifyService

router = APIRouter(prefix="/v1", tags=["identify"])


@router.post(
    "/identify",
    response_model=IdentifyResponse,
    dependencies=[Depends(enforce_rate_limit)],
    responses={
        413: {"model": ErrorOut, "description": "Upload larger than MAX_UPLOAD_MB."},
        422: {"model": ErrorOut, "description": "Audio unreadable or longer than MAX_CLIP_SEC."},
        429: {"model": ErrorOut, "description": "Rate limit exceeded; see Retry-After."},
        503: {"model": ErrorOut, "description": "Service starting or busy."},
    },
    summary="Identify the surah, ayah and reciter in a short recitation clip",
)
async def identify(
    service: Annotated[IdentifyService, Depends(get_identify_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    version: Annotated[str | None, Depends(app_version)],
    audio: Annotated[
        UploadFile, File(description="3-15 s of recitation; webm/opus, m4a, mp3 or wav")
    ],
    client: Annotated[Client | None, Form()] = None,
    debug: Annotated[bool, Form()] = False,
    previous_identify_id: Annotated[
        uuid.UUID | None,
        Form(description="Id of an earlier ambiguous result that this clip continues from."),
    ] = None,
) -> JSONResponse:
    """The clip is processed in memory and discarded when the response is sent.
    It is never written to disk, stored or logged."""
    limit = int(settings.max_upload_mb * 1024 * 1024)
    data = await audio.read(limit + 1)
    await audio.close()
    if len(data) > limit:
        IDENTIFY_REJECTED.labels("audio_too_large").inc()
        raise ApiError(413, "audio_too_large", "The audio file is too large.")

    result = await service.identify(
        data,
        client=client,
        app_version=version,
        debug=debug,
        previous_identify_id=previous_identify_id,
    )
    body = result.model_dump(mode="json")
    if body["debug"] is None:  # present only when asked for and allowed
        del body["debug"]
    return JSONResponse(body)
