"""create runs table"""

from alembic import op
import sqlalchemy as sa


revision = "0002_runs"
down_revision = "0001_conv_msg"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("user_message_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_message_id"],
            ["messages.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_runs_conversation_id", "runs", ["conversation_id"], unique=False)
    op.create_index("ix_runs_id", "runs", ["id"], unique=False)
    op.create_index("ix_runs_user_message_id", "runs", ["user_message_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_runs_user_message_id", table_name="runs")
    op.drop_index("ix_runs_id", table_name="runs")
    op.drop_index("ix_runs_conversation_id", table_name="runs")
    op.drop_table("runs")
