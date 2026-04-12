from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.services.conversation_service import ConversationService


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_conversation_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> ConversationService:
    return ConversationService(session=session)
