from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.run import Run
from app.models.tool_event import ToolEvent


class ToolEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def next_step_index(self, run: Run) -> int:
        statement = select(func.max(ToolEvent.step_index)).where(ToolEvent.run_id == run.id)
        current_max = self.session.scalar(statement)
        return int(current_max or 0) + 1

    def create_completed(
        self,
        run: Run,
        *,
        step_index: int,
        tool_name: str,
        arguments_json: str,
        result_preview: str,
    ) -> ToolEvent:
        event = ToolEvent(
            run_id=run.id,
            step_index=step_index,
            tool_name=tool_name,
            arguments_json=arguments_json,
            result_preview=result_preview,
            status="completed",
            finished_at=datetime.now(timezone.utc),
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def create_failed(
        self,
        run: Run,
        *,
        step_index: int,
        tool_name: str,
        arguments_json: str,
        error_message: str,
    ) -> ToolEvent:
        event = ToolEvent(
            run_id=run.id,
            step_index=step_index,
            tool_name=tool_name,
            arguments_json=arguments_json,
            status="failed",
            error_message=error_message,
            finished_at=datetime.now(timezone.utc),
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event
