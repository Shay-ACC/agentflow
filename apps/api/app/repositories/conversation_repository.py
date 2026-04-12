from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self) -> Conversation:
        conversation = Conversation()
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def get_by_id(self, conversation_id: int) -> Conversation | None:
        return self.session.get(Conversation, conversation_id)

    def list_all(self) -> list[Conversation]:
        statement = select(Conversation).order_by(
            Conversation.created_at.desc(),
            Conversation.id.desc(),
        )
        return list(self.session.scalars(statement).all())
