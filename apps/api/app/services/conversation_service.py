from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.message import MessageCreate


class ConversationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.conversation_repository = ConversationRepository(session)
        self.message_repository = MessageRepository(session)

    def create_conversation(self):
        return self.conversation_repository.create()

    def get_conversation(self, *, conversation_id: int):
        return self._get_conversation_or_404(conversation_id)

    def list_conversations(self):
        return self.conversation_repository.list_all()

    def create_message(self, *, conversation_id: int, payload: MessageCreate):
        self._get_conversation_or_404(conversation_id)
        return self.message_repository.create(
            conversation_id=conversation_id,
            role=payload.role,
            content=payload.content,
        )

    def list_messages(self, *, conversation_id: int):
        self._get_conversation_or_404(conversation_id)
        return self.message_repository.list_by_conversation_id(conversation_id)

    def _get_conversation_or_404(self, conversation_id: int):
        conversation = self.conversation_repository.get_by_id(conversation_id)
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        return conversation
