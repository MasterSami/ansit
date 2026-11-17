"""Reciter registry and voice gallery.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

EMBEDDING_DIM = 256  # fixed for this migration; a model change needs a new one


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "reciters",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name_ar", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=False),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("styles", postgresql.ARRAY(sa.String(16)), nullable=False),
        sa.Column("sources", postgresql.JSONB, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    )
    op.create_table(
        "gallery_clips",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "reciter_id",
            sa.String(64),
            sa.ForeignKey("reciters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("style", sa.String(16), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
    )
    op.create_index("ix_gallery_clips_voice", "gallery_clips", ["reciter_id", "style"])
    op.create_table(
        "reciter_centroids",
        sa.Column(
            "reciter_id",
            sa.String(64),
            sa.ForeignKey("reciters.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("style", sa.String(16), primary_key=True),
        sa.Column("clip_count", sa.Integer, nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("reciter_centroids")
    op.drop_index("ix_gallery_clips_voice", table_name="gallery_clips")
    op.drop_table("gallery_clips")
    op.drop_table("reciters")
