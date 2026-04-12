from fastapi import APIRouter

from app.core.config import get_settings
from app.core.db import check_database_connection
from app.core.openai import get_llm_client
from app.core.qdrant import check_qdrant_connection, get_qdrant_client
from app.core.redis import check_redis_connection, get_redis_client


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def read_health() -> dict[str, object]:
    settings = get_settings()
    database_check = check_database_connection()
    redis_check = check_redis_connection()
    qdrant_check = check_qdrant_connection()
    redis_client = get_redis_client()
    qdrant_client = get_qdrant_client()
    llm_client = get_llm_client()

    status = (
        "ok"
        if database_check.ready and redis_check.ready and qdrant_check.ready
        else "degraded"
    )

    return {
        "status": status,
        "environment": settings.project_env,
        "services": {
            "database": {
                "ready": database_check.ready,
                "error": database_check.error,
            },
            "redis": {
                "configured": redis_client.is_configured,
                "ready": redis_check.ready,
                "url": redis_client.url,
                "error": redis_check.error,
            },
            "qdrant": {
                "configured": qdrant_client.is_configured,
                "ready": qdrant_check.ready,
                "url": qdrant_client.url,
                "error": qdrant_check.error,
            },
            "llm": {
                "configured": llm_client.is_configured,
                "provider": llm_client.provider,
                "model": llm_client.model,
            },
        },
    }
