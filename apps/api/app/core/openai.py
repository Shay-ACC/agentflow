import logging
from dataclasses import dataclass

from openai import OpenAI

from app.core.config import get_settings


logger = logging.getLogger(__name__)


class LLMConfigurationError(Exception):
    pass


class LLMResponseError(Exception):
    pass


class EmbeddingConfigurationError(Exception):
    pass


class EmbeddingResponseError(Exception):
    pass


@dataclass(frozen=True)
class LLMClientInfo:
    provider: str
    api_key: str
    model: str
    base_url: str | None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key) and self.api_key != "your_openai_api_key_here"


@dataclass(frozen=True)
class EmbeddingClientInfo:
    provider: str
    api_key: str
    model: str
    base_url: str | None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key) and bool(self.model) and self.api_key != "your_openai_api_key_here"


def get_llm_client() -> LLMClientInfo:
    settings = get_settings()
    return LLMClientInfo(
        provider=settings.llm_provider,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
    )


def get_embedding_client() -> EmbeddingClientInfo:
    settings = get_settings()
    return EmbeddingClientInfo(
        provider=settings.embedding_provider,
        api_key=settings.embedding_api_key,
        model=settings.embedding_model,
        base_url=settings.embedding_base_url,
    )


def generate_assistant_reply(
    *,
    conversation_messages: list[dict[str, str]],
    system_messages: list[str] | None = None,
) -> str:
    settings = get_settings()
    client_info = get_llm_client()

    if not client_info.is_configured:
        raise LLMConfigurationError("LLM_API_KEY is not configured.")

    client = _build_openai_client(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )
    response = None
    request_input = [
        *[
            {
                "role": "system",
                "content": message,
            }
            for message in (system_messages or [])
        ],
        *[
            {
                "role": message["role"],
                "content": message["content"],
            }
            for message in conversation_messages
        ],
    ]

    logger.info(
        "LLM request starting provider=%s model=%s base_url=%s message_count=%s",
        client_info.provider,
        client_info.model,
        client_info.base_url or "default",
        len(conversation_messages),
    )

    try:
        response = client.responses.create(
            model=settings.llm_model,
            input=request_input,
        )
    except Exception as exc:
        logger.exception(
            "LLM request failed provider=%s model=%s base_url=%s exception_type=%s exception_message=%s",
            client_info.provider,
            client_info.model,
            client_info.base_url or "default",
            type(exc).__name__,
            str(exc),
        )
        raise

    output_text = (response.output_text or "").strip()
    if not output_text:
        logger.error(
            "LLM response parsing failed provider=%s model=%s base_url=%s raw_response=%s",
            client_info.provider,
            client_info.model,
            client_info.base_url or "default",
            _safe_response_preview(response),
        )
        raise LLMResponseError("The provider returned an empty assistant response.")

    return output_text


def generate_embeddings(
    *,
    texts: list[str],
) -> list[list[float]]:
    settings = get_settings()
    client_info = get_embedding_client()

    if not client_info.is_configured:
        raise EmbeddingConfigurationError("Embedding provider is not configured.")

    client = _build_openai_client(
        api_key=settings.embedding_api_key,
        base_url=settings.embedding_base_url,
    )

    logger.info(
        "Embedding request starting provider=%s model=%s base_url=%s input_count=%s",
        client_info.provider,
        client_info.model,
        client_info.base_url or "default",
        len(texts),
    )

    try:
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
    except Exception as exc:
        logger.exception(
            "Embedding request failed provider=%s model=%s base_url=%s exception_type=%s exception_message=%s",
            client_info.provider,
            client_info.model,
            client_info.base_url or "default",
            type(exc).__name__,
            str(exc),
        )
        raise

    embeddings = [list(item.embedding) for item in response.data]
    if len(embeddings) != len(texts):
        raise EmbeddingResponseError("Embedding response count did not match input count.")
    if any(len(embedding) == 0 for embedding in embeddings):
        raise EmbeddingResponseError("Embedding response contained an empty vector.")

    return embeddings


def _build_openai_client(*, api_key: str, base_url: str | None) -> OpenAI:
    client_kwargs: dict[str, str] = {
        "api_key": api_key,
    }
    if base_url:
        client_kwargs["base_url"] = base_url
    return OpenAI(**client_kwargs)


def _safe_response_preview(response: object) -> str:
    try:
        if hasattr(response, "model_dump"):
            return str(response.model_dump())
        if hasattr(response, "__dict__"):
            return str(vars(response))
        return str(response)
    except Exception as exc:
        return f"<unserializable response: {type(exc).__name__}: {exc}>"
