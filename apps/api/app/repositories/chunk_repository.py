from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.chunk import Chunk


class ChunkRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_many(
        self,
        *,
        document_id: int,
        chunk_records: list[dict[str, str | int]],
    ) -> list[Chunk]:
        chunks = [
            Chunk(
                document_id=document_id,
                chunk_index=int(record["chunk_index"]),
                content=str(record["content"]),
                content_length=int(record["content_length"]),
                qdrant_point_id=str(record["qdrant_point_id"]),
            )
            for record in chunk_records
        ]
        self.session.add_all(chunks)
        self.session.commit()
        for chunk in chunks:
            self.session.refresh(chunk)
        return chunks

    def count_all(self) -> int:
        statement = select(func.count()).select_from(Chunk)
        return int(self.session.scalar(statement) or 0)

    def delete_by_document_id(self, document_id: int) -> None:
        chunks = list(
            self.session.scalars(
                select(Chunk).where(Chunk.document_id == document_id),
            ).all(),
        )
        for chunk in chunks:
            self.session.delete(chunk)
        self.session.commit()
