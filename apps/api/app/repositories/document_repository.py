from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, document_id: int) -> Document | None:
        statement = (
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.chunks))
        )
        return self.session.scalar(statement)

    def get_by_content_hash(self, content_hash: str) -> Document | None:
        statement = (
            select(Document)
            .where(Document.content_hash == content_hash)
            .options(selectinload(Document.chunks))
        )
        return self.session.scalar(statement)

    def create(
        self,
        *,
        content_hash: str,
        filename: str,
        content_type: str | None,
        byte_size: int,
        text_length: int,
    ) -> Document:
        document = Document(
            content_hash=content_hash,
            filename=filename,
            content_type=content_type,
            byte_size=byte_size,
            text_length=text_length,
        )
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document

    def list_all(self) -> list[Document]:
        statement = (
            select(Document)
            .options(selectinload(Document.chunks))
            .order_by(Document.created_at.desc(), Document.id.desc())
        )
        return list(self.session.scalars(statement).all())

    def delete(self, document: Document) -> None:
        self.session.delete(document)
        self.session.commit()
