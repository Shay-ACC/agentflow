from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_conversation_service
from app.schemas.conversation import ConversationCreate, ConversationRead
from app.schemas.message import MessageCreate, MessageRead
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


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    conversation_id: int,
    payload: MessageCreate,
    service: ConversationServiceDep,
) -> MessageRead:
    message = service.create_message(conversation_id=conversation_id, payload=payload)
    return MessageRead.model_validate(message)


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
def list_messages(
    conversation_id: int,
    service: ConversationServiceDep,
) -> list[MessageRead]:
    messages = service.list_messages(conversation_id=conversation_id)
    return [MessageRead.model_validate(message) for message in messages]
