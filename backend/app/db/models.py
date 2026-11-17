"""Database schema: reciter registry, voice gallery, identify events and feedback.

Only embeddings are stored for a reciter's voice. No audio is ever written to
the database (privacy rule, and the source recordings are not ours to store).
"""

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.speaker.engine import EMBEDDING_DIM


class Base(DeclarativeBase):
    pass


class Reciter(Base):
    __tablename__ = "reciters"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # slug, e.g. "minshawi"
    name_ar: Mapped[str] = mapped_column(String(200))
    name_en: Mapped[str] = mapped_column(String(200))
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    styles: Mapped[list[str]] = mapped_column(ARRAY(String(16)))
    sources: Mapped[dict[str, Any]] = mapped_column(JSONB)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class GalleryClip(Base):
    """One clip's voice embedding (L2-normalized)."""

    __tablename__ = "gallery_clips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reciter_id: Mapped[str] = mapped_column(ForeignKey("reciters.id", ondelete="CASCADE"))
    style: Mapped[str] = mapped_column(String(16))
    embedding: Mapped[Any] = mapped_column(Vector(EMBEDDING_DIM))

    __table_args__ = (Index("ix_gallery_clips_voice", "reciter_id", "style"),)


class ReciterCentroid(Base):
    """Per (reciter, style) centroid of the clip embeddings (L2-normalized)."""

    __tablename__ = "reciter_centroids"

    reciter_id: Mapped[str] = mapped_column(
        ForeignKey("reciters.id", ondelete="CASCADE"), primary_key=True
    )
    style: Mapped[str] = mapped_column(String(16), primary_key=True)
    clip_count: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[Any] = mapped_column(Vector(EMBEDDING_DIM))


class IdentifyEvent(Base):
    """One identify request, for monitoring and threshold tuning.

    Deliberately holds NO audio and NO transcript: only the outcome, scores,
    timings and coarse client information.
    """

    __tablename__ = "identify_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    status: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    text_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    repeated_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reciter_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    reciter_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reciter_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    clip_sec: Mapped[float] = mapped_column(Float)
    speech_sec: Mapped[float] = mapped_column(Float)
    timings_ms: Mapped[dict[str, Any]] = mapped_column(JSONB)
    client: Mapped[str | None] = mapped_column(String(16), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(32), nullable=True)


class Feedback(Base):
    """A user's report that a result was wrong."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    identify_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    correct_surah: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct_ayah: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct_reciter_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
