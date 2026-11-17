"""POST /v1/feedback: a user reports a wrong result."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import enforce_rate_limit, get_index, get_services
from app.api.errors import ApiError
from app.api.schemas import ErrorOut, FeedbackIn, FeedbackOut
from app.core.logging import get_logger
from app.db.models import Feedback
from app.matcher.index import QuranIndex
from app.services import Services

router = APIRouter(prefix="/v1", tags=["feedback"])
log = get_logger(__name__)


@router.post(
    "/feedback",
    response_model=FeedbackOut,
    status_code=201,
    dependencies=[Depends(enforce_rate_limit)],
    responses={422: {"model": ErrorOut}, 429: {"model": ErrorOut}, 503: {"model": ErrorOut}},
)
async def submit_feedback(
    body: FeedbackIn,
    request: Request,
    index: Annotated[QuranIndex, Depends(get_index)],
    services: Annotated[Services, Depends(get_services)],
) -> FeedbackOut:
    """Stored to improve thresholds and the gallery. It holds only what is sent
    here; it is not linked to any audio, because none is kept."""
    if (body.correct_surah is None) != (body.correct_ayah is None):
        raise ApiError(
            422, "invalid_request", "Give both correct_surah and correct_ayah, or neither."
        )
    if (
        body.correct_surah is not None
        and body.correct_ayah is not None
        and body.correct_ayah > index.surahs[body.correct_surah - 1].ayah_count
    ):
        raise ApiError(
            422, "invalid_request", f"Surah {body.correct_surah} has no ayah {body.correct_ayah}."
        )
    if body.correct_reciter_id is not None and body.correct_reciter_id not in services.reciters:
        raise ApiError(422, "invalid_request", "Unknown correct_reciter_id.")

    sessions = request.app.state.deps.sessions
    if sessions is None:
        raise ApiError(503, "feedback_unavailable", "Feedback cannot be stored right now.")
    try:
        async with sessions() as session:
            session.add(Feedback(**body.model_dump()))
            await session.commit()
    except (SQLAlchemyError, OSError) as exc:
        log.warning("feedback_not_stored", error=type(exc).__name__)
        raise ApiError(
            503, "feedback_unavailable", "Feedback cannot be stored right now."
        ) from None
    return FeedbackOut(stored=True)
