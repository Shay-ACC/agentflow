from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str | None
    byte_size: int
    text_length: int
    chunk_count: int
    created_at: datetime
