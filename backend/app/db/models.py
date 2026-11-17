"""Database schema: reciter registry and voice gallery.

Only embeddings are stored for a reciter's voice. No audio is ever written to
the database (privacy rule, and the source recordings are not ours to store).
"""

from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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
