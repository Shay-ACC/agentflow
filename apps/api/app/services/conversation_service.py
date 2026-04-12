import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.openai import LLMConfigurationError, LLMResponseError, get_llm_client, generate_assistant_reply
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.run_repository import RunRepository
from app.schemas.message import MessageCreate


logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.conversation_repository = ConversationRepository(session)
        self.message_repository = MessageRepository(session)
        self.run_repository = RunRepository(session)

    def create_conversation(self):
        return self.conversation_repository.create()

    def get_conversation(self, *, conversation_id: int):
        return self._get_conversation_or_404(conversation_id)

    def list_conversations(self):
        return self.conversation_repository.list_all()

    def create_message(self, *, conversation_id: int, payload: MessageCreate):
        self._get_conversation_or_404(conversation_id)
        llm_client = get_llm_client()
        user_message = self.message_repository.create(
            conversation_id=conversation_id,
            role=payload.role,
            content=payload.content,
        )
        run = self.run_repository.create_pending(
            conversation_id=conversation_id,
            user_message_id=user_message.id,
            provider=llm_client.provider,
            model=llm_client.model,
        )
        conversation_messages = self.message_repository.list_by_conversation_id(
            conversation_id,
        )

        try:
            assistant_content = generate_assistant_reply(
                conversation_messages=[
                    {
                        "role": message.role,
                        "content": message.content,
                    }
                    for message in conversation_messages
                ],
            )
        except LLMConfigurationError as exc:
            self.run_repository.mark_failed(
                run,
                error_message=self._truncate_error_message(str(exc)),
            )
            logger.error(
                "LLM configuration error conversation_id=%s exception_type=%s exception_message=%s",
                conversation_id,
                type(exc).__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=self._build_error_detail(
                    public_message="LLM is not configured.",
                    exc=exc,
                ),
            ) from exc
        except LLMResponseError as exc:
            self.run_repository.mark_failed(
                run,
                error_message=self._truncate_error_message(str(exc)),
            )
            logger.error(
                "LLM response parsing error conversation_id=%s exception_type=%s exception_message=%s",
                conversation_id,
                type(exc).__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=self._build_error_detail(
                    public_message="LLM response parsing failed.",
                    exc=exc,
                ),
            ) from exc
        except Exception as exc:
            self.run_repository.mark_failed(
                run,
                error_message=self._truncate_error_message(str(exc)),
            )
            logger.exception(
                "LLM generation failed conversation_id=%s exception_type=%s exception_message=%s",
                conversation_id,
                type(exc).__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=self._build_error_detail(
                    public_message="Failed to generate assistant response.",
                    exc=exc,
                ),
            ) from exc

        assistant_message = self.message_repository.create(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_content,
        )
        self.run_repository.mark_completed(run)

        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
        }

    def list_messages(self, *, conversation_id: int):
        self._get_conversation_or_404(conversation_id)
        return self.message_repository.list_by_conversation_id(conversation_id)

    def list_runs(self, *, conversation_id: int):
        self._get_conversation_or_404(conversation_id)
        return self.run_repository.list_by_conversation_id(conversation_id)

    def _get_conversation_or_404(self, conversation_id: int):
        conversation = self.conversation_repository.get_by_id(conversation_id)
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        return conversation

    def _build_error_detail(self, *, public_message: str, exc: Exception) -> str:
        settings = get_settings()
        if settings.project_env == "development":
            return f"{public_message} [{type(exc).__name__}: {exc}]"
        return public_message

    def _truncate_error_message(self, message: str) -> str:
        normalized_message = message.strip() or "Unknown error."
        return normalized_message[:500]
