from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_conversation_service
from app.schemas.conversation import ConversationCreate, ConversationRead
from app.schemas.message import MessageCreate, MessageCreateResult, MessageRead
from app.schemas.run import RunRead
from app.services.conversation_service import ConversationService


router = APIRouter(prefix="/conversations", tags=["conversations"])

ConversationServiceDep = Annotated[
    ConversationService,
    Depends(get_conversation_service),
]


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(
    service: ConversationServiceDep,
    _: ConversationCreate | None = None,
) -> ConversationRead:
    conversation = service.create_conversation()
    return ConversationRead.model_validate(conversation)


@router.get("", response_model=list[ConversationRead])
def list_conversations(
    service: ConversationServiceDep,
) -> list[ConversationRead]:
    conversations = service.list_conversations()
    return [ConversationRead.model_validate(conversation) for conversation in conversations]


@router.get("/{conversation_id}", response_model=ConversationRead)
def get_conversation(
    conversation_id: int,
    service: ConversationServiceDep,
) -> ConversationRead:
    conversation = service.get_conversation(conversation_id=conversation_id)
    return ConversationRead.model_validate(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    service: ConversationServiceDep,
) -> None:
    service.delete_conversation(conversation_id=conversation_id)


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageCreateResult,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    conversation_id: int,
    payload: MessageCreate,
    service: ConversationServiceDep,
) -> MessageCreateResult:
    result = service.create_message(conversation_id=conversation_id, payload=payload)
    return MessageCreateResult(
        user_message=MessageRead.model_validate(result["user_message"]),
        assistant_message=MessageRead.model_validate(result["assistant_message"]),
    )


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
def list_messages(
    conversation_id: int,
    service: ConversationServiceDep,
) -> list[MessageRead]:
    messages = service.list_messages(conversation_id=conversation_id)
    return [MessageRead.model_validate(message) for message in messages]


@router.get("/{conversation_id}/runs", response_model=list[RunRead])
def list_runs(
    conversation_id: int,
    service: ConversationServiceDep,
) -> list[RunRead]:
    runs = service.list_runs(conversation_id=conversation_id)
    return [
        RunRead(
            id=run.id,
            conversation_id=run.conversation_id,
            user_message_id=run.user_message_id,
            user_message_preview=_build_user_message_preview(run.user_message.content),
            provider=run.provider,
            model=run.model,
            status=run.status,
            error_message=run.error_message,
            started_at=run.started_at,
            finished_at=run.finished_at,
        )
        for run in runs
    ]


def _build_user_message_preview(content: str) -> str:
    preview = " ".join(content.split())
    if len(preview) <= 80:
        return preview
    return f"{preview[:77]}..."
