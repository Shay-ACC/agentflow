from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_conversation_service
from app.schemas.run import RunRead
from app.services.conversation_service import ConversationService


router = APIRouter(prefix="/runs", tags=["runs"])
ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]


@router.get("/{run_id}", response_model=RunRead)
def get_run(run_id: int, service: ConversationServiceDep) -> RunRead:
    run = service.get_run(run_id=run_id)
    return RunRead(
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


def _build_user_message_preview(content: str) -> str:
    preview = " ".join(content.split())
    if len(preview) <= 80:
        return preview
    return f"{preview[:77]}..."
