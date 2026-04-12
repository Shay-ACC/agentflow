from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


settings = get_settings()


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@dataclass(frozen=True)
class ServiceCheckResult:
    ready: bool
    error: str | None = None


def check_database_connection() -> ServiceCheckResult:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return ServiceCheckResult(ready=True)
    except Exception as exc:
        return ServiceCheckResult(ready=False, error=str(exc))
