from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    user_message_id: int
    provider: str
    model: str
    status: str
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None
