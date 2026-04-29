import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.openai import (
    EmbeddingConfigurationError,
    EmbeddingResponseError,
    LLMConfigurationError,
    LLMResponseError,
    ToolCallCompatibilityError,
    generate_assistant_reply_from_tool_results,
    generate_assistant_reply_or_tool_calls,
    generate_embeddings,
    get_llm_client,
)
from app.core.qdrant import QdrantCollectionNotFoundError, search_chunk_points
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.run_repository import RunRepository
from app.repositories.tool_event_repository import ToolEventRepository
from app.schemas.message import MessageCreate
from app.services.tool_service import ToolExecutionError, ToolService


logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.conversation_repository = ConversationRepository(session)
        self.message_repository = MessageRepository(session)
        self.run_repository = RunRepository(session)
        self.tool_event_repository = ToolEventRepository(session)
        self.chunk_repository = ChunkRepository(session)
        self.tool_service = ToolService(session)

    def create_conversation(self):
        return self.conversation_repository.create()

    def get_conversation(self, *, conversation_id: int):
        return self._get_conversation_or_404(conversation_id)

    def list_conversations(self):
        return self.conversation_repository.list_all()

    def delete_conversation(self, *, conversation_id: int) -> None:
        conversation = self._get_conversation_or_404(conversation_id)
        self.conversation_repository.delete(conversation)

    def create_message(self, *, conversation_id: int, payload: MessageCreate):
        self._get_conversation_or_404(conversation_id)
        llm_client = get_llm_client()
        user_message = self.message_repository.create(
            conversation_id=conversation_id,
            role=payload.role,
            content=payload.content,
        )
        run = self.run_repository.create_pending(
            conversation_id=conversation_id,
            user_message_id=user_message.id,
            provider=llm_client.provider,
            model=llm_client.model,
        )
        conversation_messages = self.message_repository.list_by_conversation_id(
            conversation_id,
        )
        system_messages = self._build_retrieval_system_messages(
            run=run,
            conversation_id=conversation_id,
            user_message_content=payload.content,
        )

        try:
            assistant_content = self._generate_assistant_content(
                run=run,
                conversation_messages=conversation_messages,
                user_message_content=payload.content,
                system_messages=system_messages,
            )
        except ToolCallCompatibilityError as exc:
            self.tool_event_repository.create_failed(
                run,
                step_index=self.tool_event_repository.next_step_index(run),
                tool_name="provider_tool_call",
                arguments_json="{}",
                error_message=self._truncate_error_message(str(exc)),
            )
            self.run_repository.mark_failed(
                run,
                error_message=self._truncate_error_message(str(exc)),
            )
            logger.error(
                "LLM tool call compatibility error conversation_id=%s exception_type=%s exception_message=%s",
                conversation_id,
                type(exc).__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=self._build_error_detail(
                    public_message="LLM tool call compatibility failed.",
                    exc=exc,
                ),
            ) from exc
        except ToolExecutionError as exc:
            self.run_repository.mark_failed(
                run,
                error_message=self._truncate_error_message(str(exc)),
            )
            logger.error(
                "Internal tool execution failed conversation_id=%s exception_type=%s exception_message=%s",
                conversation_id,
                type(exc).__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=self._build_error_detail(
                    public_message="Internal tool execution failed.",
                    exc=exc,
                ),
            ) from exc
        except LLMConfigurationError as exc:
            self.run_repository.mark_failed(
                run,
                error_message=self._truncate_error_message(str(exc)),
            )
            logger.error(
                "LLM configuration error conversation_id=%s exception_type=%s exception_message=%s",
                conversation_id,
                type(exc).__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=self._build_error_detail(
                    public_message="LLM is not configured.",
                    exc=exc,
                ),
            ) from exc
        except LLMResponseError as exc:
            self.run_repository.mark_failed(
                run,
                error_message=self._truncate_error_message(str(exc)),
            )
            logger.error(
                "LLM response parsing error conversation_id=%s exception_type=%s exception_message=%s",
                conversation_id,
                type(exc).__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=self._build_error_detail(
                    public_message="LLM response parsing failed.",
                    exc=exc,
                ),
            ) from exc
        except Exception as exc:
            self.run_repository.mark_failed(
                run,
                error_message=self._truncate_error_message(str(exc)),
            )
            logger.exception(
                "LLM generation failed conversation_id=%s exception_type=%s exception_message=%s",
                conversation_id,
                type(exc).__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=self._build_error_detail(
                    public_message="Failed to generate assistant response.",
                    exc=exc,
                ),
            ) from exc

        assistant_message = self.message_repository.create(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_content,
        )
        self.run_repository.mark_completed(run)

        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
        }

    def list_messages(self, *, conversation_id: int):
        self._get_conversation_or_404(conversation_id)
        return self.message_repository.list_by_conversation_id(conversation_id)

    def list_runs(self, *, conversation_id: int):
        self._get_conversation_or_404(conversation_id)
        return self.run_repository.list_by_conversation_id(conversation_id)

    def get_run(self, *, run_id: int):
        run = self.run_repository.get_by_id(run_id)
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Run not found.",
            )
        return run

    def _get_conversation_or_404(self, conversation_id: int):
        conversation = self.conversation_repository.get_by_id(conversation_id)
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        return conversation

    def _build_error_detail(self, *, public_message: str, exc: Exception) -> str:
        settings = get_settings()
        if settings.project_env == "development":
            return f"{public_message} [{type(exc).__name__}: {exc}]"
        return public_message

    def _truncate_error_message(self, message: str) -> str:
        normalized_message = message.strip() or "Unknown error."
        return normalized_message[:500]

    def _generate_assistant_content(
        self,
        *,
        run,
        conversation_messages: list,
        user_message_content: str,
        system_messages: list[str],
    ) -> str:
        decision = generate_assistant_reply_or_tool_calls(
            conversation_messages=[
                {
                    "role": message.role,
                    "content": message.content,
                }
                for message in conversation_messages
            ],
            system_messages=[self._build_tool_system_message(), *system_messages],
            tools=self.tool_service.get_tool_definitions(),
        )

        if not decision.tool_calls:
            if decision.assistant_content:
                return decision.assistant_content
            raise LLMResponseError("The provider returned no assistant response or tool call.")

        tool_results: list[dict[str, str]] = []
        for step_index, tool_call in enumerate(decision.tool_calls, start=1):
            try:
                tool_result = self.tool_service.execute(
                    tool_name=tool_call.name,
                    arguments=tool_call.arguments,
                )
            except Exception as exc:
                self.tool_event_repository.create_failed(
                    run,
                    step_index=step_index,
                    tool_name=tool_call.name,
                    arguments_json=tool_call.arguments_json,
                    error_message=self._truncate_error_message(str(exc)),
                )
                raise ToolExecutionError(str(exc)) from exc

            self.tool_event_repository.create_completed(
                run,
                step_index=step_index,
                tool_name=tool_call.name,
                arguments_json=tool_call.arguments_json,
                result_preview=tool_result.result_preview,
            )
            tool_results.append(
                {
                    "call_id": tool_call.call_id,
                    "tool_name": tool_call.name,
                    "output": tool_result.output_json,
                },
            )
            logger.info(
                "Internal tool executed run_id=%s step_index=%s tool_name=%s",
                run.id,
                step_index,
                tool_call.name,
            )

        if decision.response_id is None:
            raise ToolCallCompatibilityError("Provider did not return a response id for tool output submission.")

        return generate_assistant_reply_from_tool_results(
            previous_response_id=decision.response_id,
            tool_results=tool_results,
            user_message_content=user_message_content,
        )

    def _build_tool_system_message(self) -> str:
        return "\n".join(
            [
                "You can call internal tools when they are useful.",
                "Use list_documents when the user asks about uploaded documents.",
                "Use get_run_detail when the user asks to inspect a run by run_id.",
                "Use search_documents when the user asks to search indexed document chunks.",
                "Do not claim tool results unless you called the relevant tool.",
            ],
        )

    def _build_retrieval_system_messages(
        self,
        *,
        run,
        conversation_id: int,
        user_message_content: str,
    ) -> list[str]:
        if self.chunk_repository.count_all() == 0:
            self._log_retrieval_skipped(
                conversation_id=conversation_id,
                reason="no_indexed_chunks",
            )
            return []

        settings = get_settings()

        try:
            query_embedding = generate_embeddings(texts=[user_message_content])[0]
            retrieved_chunks = search_chunk_points(
                query_vector=query_embedding,
                limit=settings.rag_top_k,
            )
        except (EmbeddingConfigurationError, EmbeddingResponseError) as exc:
            self._log_retrieval_skipped(
                conversation_id=conversation_id,
                reason=f"embedding_error:{type(exc).__name__}",
            )
            return []
        except QdrantCollectionNotFoundError:
            self._log_retrieval_skipped(
                conversation_id=conversation_id,
                reason="no_collection",
            )
            return []
        except Exception as exc:
            self._log_retrieval_skipped(
                conversation_id=conversation_id,
                reason=f"retrieval_error:{type(exc).__name__}",
            )
            return []

        if not retrieved_chunks:
            logger.info(
                "RAG retrieval returned_zero_chunks conversation_id=%s reason=no_results retrieved_chunk_count=0 chunk_ids=[] document_ids=[]",
                conversation_id,
            )
            return []

        self.run_repository.create_sources(
            run,
            source_records=[
                {
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "rank": rank,
                    "content_preview": self._build_content_preview(chunk.content),
                }
                for rank, chunk in enumerate(retrieved_chunks, start=1)
            ],
        )

        self._log_retrieval_used(
            conversation_id=conversation_id,
            retrieved_chunks=retrieved_chunks,
        )

        return [
            "\n\n".join(
                [
                    "Use the retrieved context below when it is relevant to the user request.",
                    "If the context is not relevant, answer from the conversation alone.",
                    "Retrieved context:",
                    *[
                        (
                            f"[Document {chunk.document_id} | Chunk {chunk.chunk_id} | Index {chunk.chunk_index}]\n"
                            f"{chunk.content}"
                        )
                        for chunk in retrieved_chunks
                    ],
                ],
            ),
        ]

    def _log_retrieval_skipped(self, *, conversation_id: int, reason: str) -> None:
        logger.info(
            "RAG retrieval skipped conversation_id=%s reason=%s retrieved_chunk_count=0 chunk_ids=[] document_ids=[]",
            conversation_id,
            reason,
        )

    def _log_retrieval_used(self, *, conversation_id: int, retrieved_chunks: list) -> None:
        logger.info(
            "RAG retrieval used conversation_id=%s retrieved_chunk_count=%s chunk_ids=%s document_ids=%s",
            conversation_id,
            len(retrieved_chunks),
            [chunk.chunk_id for chunk in retrieved_chunks],
            [chunk.document_id for chunk in retrieved_chunks],
        )

    def _build_content_preview(self, content: str) -> str:
        preview = " ".join(content.split())
        if len(preview) <= 240:
            return preview
        return f"{preview[:237]}..."
