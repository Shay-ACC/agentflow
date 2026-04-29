"""create tool events table

Revision ID: 0006_create_tool_events_table
Revises: 0005_create_run_sources_table
Create Date: 2026-04-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0006_create_tool_events_table"
down_revision: str | None = "0005_create_run_sources_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tool_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("arguments_json", sa.Text(), nullable=False),
        sa.Column("result_preview", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "step_index", name="uq_tool_events_run_step"),
    )
    op.create_index(op.f("ix_tool_events_id"), "tool_events", ["id"], unique=False)
    op.create_index(op.f("ix_tool_events_run_id"), "tool_events", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tool_events_run_id"), table_name="tool_events")
    op.drop_index(op.f("ix_tool_events_id"), table_name="tool_events")
    op.drop_table("tool_events")
