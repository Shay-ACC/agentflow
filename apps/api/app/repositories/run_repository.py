from sqlalchemy import select
from datetime import datetime, timezone

from sqlalchemy.orm import Session, selectinload

from app.models.run import Run
from app.models.run_source import RunSource


class RunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, run_id: int) -> Run | None:
        statement = (
            select(Run)
            .where(Run.id == run_id)
            .options(selectinload(Run.user_message), selectinload(Run.sources))
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

    def create_sources(
        self,
        run: Run,
        *,
        source_records: list[dict[str, int | str]],
    ) -> list[RunSource]:
        seen_chunk_ids: set[int] = set()
        sources: list[RunSource] = []

        for record in source_records:
            chunk_id = int(record["chunk_id"])
            if chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(chunk_id)
            sources.append(
                RunSource(
                    run_id=run.id,
                    document_id=int(record["document_id"]),
                    chunk_id=chunk_id,
                    chunk_index=int(record["chunk_index"]),
                    rank=int(record["rank"]),
                    content_preview=str(record["content_preview"]),
                ),
            )

        if not sources:
            return []

        self.session.add_all(sources)
        self.session.commit()
        for source in sources:
            self.session.refresh(source)
        self.session.refresh(run)
        return sources

    def list_by_conversation_id(self, conversation_id: int) -> list[Run]:
        statement = (
            select(Run)
            .where(Run.conversation_id == conversation_id)
            .options(selectinload(Run.user_message))
            .order_by(Run.started_at.desc(), Run.id.desc())
        )
        return list(self.session.scalars(statement).all())
