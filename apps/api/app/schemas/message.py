from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    role: Literal["user", "assistant", "system"] = Field(default="user")
    content: str = Field(min_length=1)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime


class MessageCreateResult(BaseModel):
    user_message: MessageRead
    assistant_message: MessageRead
