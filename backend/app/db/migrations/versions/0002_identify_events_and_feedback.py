"""Identify events and feedback.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "identify_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("reason", sa.String(32), nullable=True),
        sa.Column("text_confidence", sa.Float, nullable=True),
        sa.Column("repeated_count", sa.Integer, nullable=True),
        sa.Column("reciter_status", sa.String(16), nullable=True),
        sa.Column("reciter_id", sa.String(64), nullable=True),
        sa.Column("reciter_similarity", sa.Float, nullable=True),
        sa.Column("clip_sec", sa.Float, nullable=False),
        sa.Column("speech_sec", sa.Float, nullable=False),
        sa.Column("timings_ms", postgresql.JSONB, nullable=False),
        sa.Column("client", sa.String(16), nullable=True),
        sa.Column("app_version", sa.String(32), nullable=True),
    )
    op.create_index("ix_identify_events_created_at", "identify_events", ["created_at"])
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("identify_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("correct_surah", sa.Integer, nullable=True),
        sa.Column("correct_ayah", sa.Integer, nullable=True),
        sa.Column("correct_reciter_id", sa.String(64), nullable=True),
    )
    op.create_index("ix_feedback_identify_id", "feedback", ["identify_id"])


def downgrade() -> None:
    op.drop_index("ix_feedback_identify_id", table_name="feedback")
    op.drop_table("feedback")
    op.drop_index("ix_identify_events_created_at", table_name="identify_events")
    op.drop_table("identify_events")
