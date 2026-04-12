from datetime import datetime
from typing import Literal

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


RunStatus = Literal["pending", "completed", "failed"]


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(length=64), nullable=False)
    model: Mapped[str] = mapped_column(String(length=128), nullable=False)
    status: Mapped[str] = mapped_column(String(length=32), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="runs")
    user_message: Mapped["Message"] = relationship(back_populates="run")
    sources: Mapped[list["RunSource"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="RunSource.rank",
    )
