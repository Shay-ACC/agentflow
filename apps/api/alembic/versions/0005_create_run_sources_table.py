"""create run sources table

Revision ID: 0005_create_run_sources_table
Revises: 0004_add_document_content_hash
Create Date: 2026-04-12 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0005_create_run_sources_table"
down_revision: str | None = "0004_add_document_content_hash"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "run_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("content_preview", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "chunk_id", name="uq_run_sources_run_chunk"),
    )
    op.create_index(op.f("ix_run_sources_id"), "run_sources", ["id"], unique=False)
    op.create_index(op.f("ix_run_sources_run_id"), "run_sources", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_run_sources_run_id"), table_name="run_sources")
    op.drop_index(op.f("ix_run_sources_id"), table_name="run_sources")
    op.drop_table("run_sources")
