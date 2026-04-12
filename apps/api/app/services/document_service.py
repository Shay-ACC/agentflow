import logging
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.openai import (
    EmbeddingConfigurationError,
    EmbeddingResponseError,
    generate_embeddings,
)
from app.core.qdrant import QdrantChunkPoint, delete_chunk_points, ensure_chunk_collection, upsert_chunk_points
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository


logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.document_repository = DocumentRepository(session)
        self.chunk_repository = ChunkRepository(session)

    async def upload_document(self, *, file: UploadFile):
        filename = file.filename or "document.txt"
        _get_supported_extension(filename)
        raw_bytes = await file.read()
        text = _extract_text(raw_bytes)
        chunks = _chunk_text(text)

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file did not contain any indexable text.",
            )

        try:
            embeddings = generate_embeddings(texts=chunks)
        except EmbeddingConfigurationError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Embedding provider is not configured. [{type(exc).__name__}: {exc}]",
            ) from exc
        except EmbeddingResponseError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Embedding generation failed. [{type(exc).__name__}: {exc}]",
            ) from exc
        except Exception as exc:
            logger.exception(
                "Document embedding failed filename=%s exception_type=%s exception_message=%s",
                filename,
                type(exc).__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Embedding generation failed. [{type(exc).__name__}: {exc}]",
            ) from exc

        try:
            ensure_chunk_collection(vector_size=len(embeddings[0]))
        except Exception as exc:
            logger.exception(
                "Qdrant collection setup failed filename=%s exception_type=%s exception_message=%s",
                filename,
                type(exc).__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Qdrant collection setup failed. [{type(exc).__name__}: {exc}]",
            ) from exc

        document = self.document_repository.create(
            filename=filename,
            content_type=file.content_type,
            byte_size=len(raw_bytes),
            text_length=len(text),
        )

        chunk_records = [
            {
                "chunk_index": index,
                "content": chunk_content,
                "content_length": len(chunk_content),
                "qdrant_point_id": uuid.uuid4().hex,
            }
            for index, chunk_content in enumerate(chunks)
        ]
        chunk_models = self.chunk_repository.create_many(
            document_id=document.id,
            chunk_records=chunk_records,
        )

        try:
            upsert_chunk_points(
                [
                    QdrantChunkPoint(
                        point_id=chunk.qdrant_point_id,
                        vector=embedding,
                        document_id=document.id,
                        chunk_id=chunk.id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                    )
                    for chunk, embedding in zip(chunk_models, embeddings, strict=True)
                ],
            )
        except Exception as exc:
            try:
                delete_chunk_points([chunk.qdrant_point_id for chunk in chunk_models])
            except Exception:
                pass
            self.chunk_repository.delete_by_document_id(document.id)
            self.document_repository.delete(document)
            logger.exception(
                "Qdrant upsert failed filename=%s document_id=%s exception_type=%s exception_message=%s",
                filename,
                document.id,
                type(exc).__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Qdrant indexing failed. [{type(exc).__name__}: {exc}]",
            ) from exc

        return self.document_repository.list_all()[0]

    def list_documents(self):
        return self.document_repository.list_all()


def _get_supported_extension(filename: str) -> str:
    lowered = filename.lower()
    if lowered.endswith(".txt"):
        return ".txt"
    if lowered.endswith(".md"):
        return ".md"
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Only .txt and .md uploads are supported in v1.",
    )


def _extract_text(raw_bytes: bytes) -> str:
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file must be UTF-8 encoded text.",
        ) from exc

    normalized = text.strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )
    return normalized


def _chunk_text(text: str) -> list[str]:
    settings = get_settings()
    chunk_size = settings.rag_chunk_size
    overlap = min(settings.rag_chunk_overlap, max(chunk_size - 1, 0))
    normalized = "\n".join(line.rstrip() for line in text.splitlines()).strip()

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        if end < len(normalized):
            last_break = max(
                normalized.rfind("\n\n", start, end),
                normalized.rfind(" ", start, end),
            )
            if last_break > start + max(chunk_size // 3, 1):
                end = last_break

        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)

    return chunks
