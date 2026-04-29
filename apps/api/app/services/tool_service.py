import json
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.openai import (
    EmbeddingConfigurationError,
    EmbeddingResponseError,
    generate_embeddings,
)
from app.core.qdrant import QdrantCollectionNotFoundError, search_chunk_points
from app.repositories.document_repository import DocumentRepository
from app.repositories.run_repository import RunRepository


logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    pass


@dataclass(frozen=True)
class ToolExecutionResult:
    output_json: str
    result_preview: str


class ToolService:
    def __init__(self, session: Session) -> None:
        self.document_repository = DocumentRepository(session)
        self.run_repository = RunRepository(session)

    def get_tool_definitions(self) -> list[dict[str, object]]:
        return [
            {
                "type": "function",
                "name": "list_documents",
                "description": "List uploaded document records available to the application.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
            {
                "type": "function",
                "name": "get_run_detail",
                "description": "Get compact detail for a previous run by run_id.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "run_id": {
                            "type": "integer",
                            "description": "The run id to inspect.",
                        },
                    },
                    "required": ["run_id"],
                    "additionalProperties": False,
                },
            },
            {
                "type": "function",
                "name": "search_documents",
                "description": "Search indexed document chunks for a specific query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for indexed document chunks.",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Maximum number of chunk matches to return.",
                        },
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        ]

    def execute(self, *, tool_name: str, arguments: dict[str, object]) -> ToolExecutionResult:
        if tool_name == "list_documents":
            result = self._list_documents()
        elif tool_name == "get_run_detail":
            result = self._get_run_detail(arguments)
        elif tool_name == "search_documents":
            result = self._search_documents(arguments)
        else:
            raise ToolExecutionError(f"Unknown internal tool: {tool_name}")

        output_json = json.dumps(result, ensure_ascii=True, default=str)
        return ToolExecutionResult(
            output_json=output_json,
            result_preview=_build_result_preview(output_json),
        )

    def _list_documents(self) -> dict[str, object]:
        documents = self.document_repository.list_all()
        return {
            "documents": [
                {
                    "id": document.id,
                    "filename": document.filename,
                    "chunk_count": document.chunk_count,
                    "created_at": document.created_at.isoformat(),
                }
                for document in documents
            ],
        }

    def _get_run_detail(self, arguments: dict[str, object]) -> dict[str, object]:
        run_id = _get_required_int(arguments, "run_id")
        run = self.run_repository.get_by_id(run_id)
        if run is None:
            raise ToolExecutionError(f"Run {run_id} was not found.")

        return {
            "id": run.id,
            "conversation_id": run.conversation_id,
            "user_message_id": run.user_message_id,
            "provider": run.provider,
            "model": run.model,
            "status": run.status,
            "error_message": run.error_message,
            "source_count": len(run.sources),
            "tool_event_count": len(run.tool_events),
            "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        }

    def _search_documents(self, arguments: dict[str, object]) -> dict[str, object]:
        query = _get_required_string(arguments, "query")
        settings = get_settings()
        top_k = _get_optional_int(arguments, "top_k", default=settings.rag_top_k)
        top_k = max(1, min(top_k, 10))

        try:
            query_embedding = generate_embeddings(texts=[query])[0]
            chunks = search_chunk_points(query_vector=query_embedding, limit=top_k)
        except (EmbeddingConfigurationError, EmbeddingResponseError) as exc:
            logger.info(
                "Tool search_documents skipped reason=embedding_error:%s",
                type(exc).__name__,
            )
            return {"matches": [], "skipped_reason": f"embedding_error:{type(exc).__name__}"}
        except QdrantCollectionNotFoundError:
            return {"matches": [], "skipped_reason": "no_collection"}

        return {
            "matches": [
                {
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "score": chunk.score,
                    "content_preview": _build_content_preview(chunk.content),
                }
                for chunk in chunks
            ],
        }


def _get_required_int(arguments: dict[str, object], key: str) -> int:
    value = arguments.get(key)
    if not isinstance(value, int):
        raise ToolExecutionError(f"Tool argument '{key}' must be an integer.")
    return value


def _get_optional_int(arguments: dict[str, object], key: str, *, default: int) -> int:
    value = arguments.get(key, default)
    if not isinstance(value, int):
        raise ToolExecutionError(f"Tool argument '{key}' must be an integer.")
    return value


def _get_required_string(arguments: dict[str, object], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ToolExecutionError(f"Tool argument '{key}' must be a non-empty string.")
    return value.strip()


def _build_content_preview(content: str) -> str:
    preview = " ".join(content.split())
    if len(preview) <= 240:
        return preview
    return f"{preview[:237]}..."


def _build_result_preview(output_json: str) -> str:
    preview = " ".join(output_json.split())
    if len(preview) <= 300:
        return preview
    return f"{preview[:297]}..."
