from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        filename: str,
        content_type: str | None,
        byte_size: int,
        text_length: int,
    ) -> Document:
        document = Document(
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
