"""add document content hash

Revision ID: 0004_add_document_content_hash
Revises: 0003_create_documents_and_chunks
Create Date: 2026-04-12 00:00:00.000000
"""

from collections.abc import Sequence
import hashlib

import sqlalchemy as sa
from alembic import op


revision: str = "0004_add_document_content_hash"
down_revision: str | None = "0003_create_documents_and_chunks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("content_hash", sa.String(length=64), nullable=True))

    connection = op.get_bind()
    document_rows = connection.execute(
        sa.text("SELECT id FROM documents ORDER BY id ASC"),
    ).mappings()

    seen_hashes: set[str] = set()
    for row in document_rows:
        document_id = int(row["id"])
        chunk_rows = connection.execute(
            sa.text(
                """
                SELECT content
                FROM chunks
                WHERE document_id = :document_id
                ORDER BY chunk_index ASC, id ASC
                """,
            ),
            {"document_id": document_id},
        ).scalars().all()

        if chunk_rows:
            normalized_text = _reconstruct_text(list(chunk_rows))
            base_hash = _compute_hash(normalized_text)
        else:
            base_hash = _compute_hash(f"legacy-empty-document:{document_id}")

        assigned_hash = base_hash
        if assigned_hash in seen_hashes:
            assigned_hash = _compute_hash(f"{base_hash}:legacy-duplicate:{document_id}")

        seen_hashes.add(assigned_hash)
        connection.execute(
            sa.text(
                "UPDATE documents SET content_hash = :content_hash WHERE id = :document_id",
            ),
            {
                "content_hash": assigned_hash,
                "document_id": document_id,
            },
        )

    op.alter_column("documents", "content_hash", nullable=False)
    op.create_index(
        op.f("ix_documents_content_hash"),
        "documents",
        ["content_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_content_hash"), table_name="documents")
    op.drop_column("documents", "content_hash")


def _compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _reconstruct_text(chunks: list[str]) -> str:
    reconstructed = chunks[0]
    for chunk in chunks[1:]:
        reconstructed = _merge_with_overlap(reconstructed, chunk)
    return reconstructed.strip()


def _merge_with_overlap(left: str, right: str) -> str:
    max_overlap = min(len(left), len(right))
    for overlap_size in range(max_overlap, 0, -1):
        if left[-overlap_size:] == right[:overlap_size]:
            return f"{left}{right[overlap_size:]}"
    return f"{left}\n{right}"
