from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ToolEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    step_index: int
    tool_name: str
    arguments_json: str
    result_preview: str | None
    status: str
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None
