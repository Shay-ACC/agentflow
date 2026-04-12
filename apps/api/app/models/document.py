from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(length=255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(length=255), nullable=True)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    text_length: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Chunk.chunk_index",
    )

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)
