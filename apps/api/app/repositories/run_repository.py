from sqlalchemy import select
from datetime import datetime, timezone

from sqlalchemy.orm import Session, selectinload

from app.models.run import Run


class RunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, run_id: int) -> Run | None:
        statement = (
            select(Run)
            .where(Run.id == run_id)
            .options(selectinload(Run.user_message))
        )
        return self.session.scalar(statement)

    def create_pending(
        self,
        *,
        conversation_id: int,
        user_message_id: int,
        provider: str,
        model: str,
    ) -> Run:
        run = Run(
            conversation_id=conversation_id,
            user_message_id=user_message_id,
            provider=provider,
            model=model,
            status="pending",
        )
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def mark_completed(self, run: Run) -> Run:
        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = None
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def mark_failed(self, run: Run, *, error_message: str) -> Run:
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = error_message
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def list_by_conversation_id(self, conversation_id: int) -> list[Run]:
        statement = (
            select(Run)
            .where(Run.conversation_id == conversation_id)
            .options(selectinload(Run.user_message))
            .order_by(Run.started_at.desc(), Run.id.desc())
        )
        return list(self.session.scalars(statement).all())
