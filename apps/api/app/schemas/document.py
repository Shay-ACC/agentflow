from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


DocumentIndexStatus = Literal["indexed", "index_missing"]


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str | None
    byte_size: int
    text_length: int
    chunk_count: int
    index_status: DocumentIndexStatus
    created_at: datetime


class DocumentUploadResult(BaseModel):
    document: DocumentRead
    deduplicated: bool
