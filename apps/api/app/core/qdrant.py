import json
from dataclasses import dataclass
from urllib import error, request

from app.core.config import get_settings
from app.core.db import ServiceCheckResult


class QdrantCollectionNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class QdrantClientPlaceholder:
    url: str

    @property
    def is_configured(self) -> bool:
        return bool(self.url)


def get_qdrant_client() -> QdrantClientPlaceholder:
    settings = get_settings()
    return QdrantClientPlaceholder(url=settings.qdrant_url)


@dataclass(frozen=True)
class QdrantChunkPoint:
    point_id: str
    vector: list[float]
    document_id: int
    chunk_id: int
    chunk_index: int
    content: str


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: int
    chunk_id: int
    chunk_index: int
    content: str
    score: float


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


def ensure_chunk_collection(vector_size: int) -> None:
    settings = get_settings()
    collection_name = settings.qdrant_collection_name

    try:
        _qdrant_request("GET", f"/collections/{collection_name}")
        return
    except error.HTTPError as exc:
        if exc.code != 404:
            raise

    _qdrant_request(
        "PUT",
        f"/collections/{collection_name}",
        payload={
            "vectors": {
                "size": vector_size,
                "distance": "Cosine",
            },
        },
    )


def chunk_collection_exists() -> bool:
    settings = get_settings()

    try:
        _qdrant_request("GET", f"/collections/{settings.qdrant_collection_name}")
        return True
    except error.HTTPError as exc:
        if exc.code == 404:
            return False
        raise


def upsert_chunk_points(points: list[QdrantChunkPoint]) -> None:
    if not points:
        return

    settings = get_settings()
    _qdrant_request(
        "PUT",
        f"/collections/{settings.qdrant_collection_name}/points?wait=true",
        payload={
            "points": [
                {
                    "id": point.point_id,
                    "vector": point.vector,
                    "payload": {
                        "document_id": point.document_id,
                        "chunk_id": point.chunk_id,
                        "chunk_index": point.chunk_index,
                        "content": point.content,
                    },
                }
                for point in points
            ],
        },
    )


def search_chunk_points(
    *,
    query_vector: list[float],
    limit: int,
) -> list[RetrievedChunk]:
    settings = get_settings()
    try:
        response = _qdrant_request(
            "POST",
            f"/collections/{settings.qdrant_collection_name}/points/search",
            payload={
                "vector": query_vector,
                "limit": limit,
                "with_payload": True,
            },
        )
    except error.HTTPError as exc:
        if exc.code == 404:
            raise QdrantCollectionNotFoundError(
                f"Collection '{settings.qdrant_collection_name}' does not exist.",
            ) from exc
        raise

    results = response.get("result", [])
    return [
        RetrievedChunk(
            document_id=int(item["payload"]["document_id"]),
            chunk_id=int(item["payload"]["chunk_id"]),
            chunk_index=int(item["payload"]["chunk_index"]),
            content=str(item["payload"]["content"]),
            score=float(item.get("score") or 0.0),
        )
        for item in results
        if item.get("payload")
    ]


def delete_chunk_points(point_ids: list[str]) -> None:
    if not point_ids:
        return

    settings = get_settings()
    try:
        _qdrant_request(
            "POST",
            f"/collections/{settings.qdrant_collection_name}/points/delete?wait=true",
            payload={
                "points": point_ids,
            },
        )
    except error.HTTPError as exc:
        if exc.code == 404:
            return
        raise


def _qdrant_request(
    method: str,
    path: str,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    client = get_qdrant_client()
    url = f"{client.url.rstrip('/')}{path}"
    data = None
    headers = {}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, data=data, headers=headers, method=method)

    with request.urlopen(req, timeout=10) as response:
        body = response.read()
        if not body:
            return {}
        return json.loads(body.decode("utf-8"))
