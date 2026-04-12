from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RunSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: int
    chunk_id: int
    chunk_index: int
    rank: int
    content_preview: str


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    user_message_id: int
    user_message_preview: str
    provider: str
    model: str
    status: str
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class RunDetailRead(RunRead):
    sources: list[RunSourceRead]
