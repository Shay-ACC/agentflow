from dataclasses import dataclass
from urllib import error, request

from app.core.config import get_settings
from app.core.db import ServiceCheckResult


@dataclass(frozen=True)
class QdrantClientPlaceholder:
    url: str

    @property
    def is_configured(self) -> bool:
        return bool(self.url)


def get_qdrant_client() -> QdrantClientPlaceholder:
    settings = get_settings()
    return QdrantClientPlaceholder(url=settings.qdrant_url)


def check_qdrant_connection() -> ServiceCheckResult:
    client = get_qdrant_client()
    if not client.is_configured:
        return ServiceCheckResult(ready=False, error="QDRANT_URL is not configured.")

    url = f"{client.url.rstrip('/')}/collections"

    try:
        with request.urlopen(url, timeout=2) as response:
            if 200 <= response.status < 300:
                return ServiceCheckResult(ready=True)
            return ServiceCheckResult(
                ready=False,
                error=f"Unexpected status code: {response.status}",
            )
    except error.URLError as exc:
        return ServiceCheckResult(ready=False, error=str(exc.reason))
    except Exception as exc:
        return ServiceCheckResult(ready=False, error=str(exc))
