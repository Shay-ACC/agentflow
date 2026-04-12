from dataclasses import dataclass

from redis import Redis

from app.core.config import get_settings
from app.core.db import ServiceCheckResult


@dataclass(frozen=True)
class RedisClientPlaceholder:
    url: str

    @property
    def is_configured(self) -> bool:
        return bool(self.url)


def get_redis_client() -> RedisClientPlaceholder:
    settings = get_settings()
    return RedisClientPlaceholder(url=settings.redis_url)


def check_redis_connection() -> ServiceCheckResult:
    client = get_redis_client()
    if not client.is_configured:
        return ServiceCheckResult(ready=False, error="REDIS_URL is not configured.")

    try:
        redis_client = Redis.from_url(client.url, socket_connect_timeout=2, socket_timeout=2)
        redis_client.ping()
        return ServiceCheckResult(ready=True)
    except Exception as exc:
        return ServiceCheckResult(ready=False, error=str(exc))
