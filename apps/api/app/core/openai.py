import logging
import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from app.core.config import get_settings


logger = logging.getLogger(__name__)


class LLMConfigurationError(Exception):
    pass


class LLMResponseError(Exception):
    pass


class ToolCallCompatibilityError(Exception):
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


@dataclass(frozen=True)
class ToolCallRequest:
    call_id: str
    name: str
    arguments: dict[str, Any]
    arguments_json: str


@dataclass(frozen=True)
class ToolCallDecision:
    assistant_content: str | None
    response_id: str | None
    tool_calls: list[ToolCallRequest]


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

    output_text = _extract_response_text(response)
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


def generate_assistant_reply_or_tool_calls(
    *,
    conversation_messages: list[dict[str, str]],
    system_messages: list[str] | None = None,
    tools: list[dict[str, object]],
) -> ToolCallDecision:
    settings = get_settings()
    client_info = get_llm_client()

    if not client_info.is_configured:
        raise LLMConfigurationError("LLM_API_KEY is not configured.")

    client = _build_openai_client(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )
    request_input = _build_request_input(
        conversation_messages=conversation_messages,
        system_messages=system_messages,
    )

    logger.info(
        "LLM tool request starting provider=%s model=%s base_url=%s tool_count=%s message_count=%s",
        client_info.provider,
        client_info.model,
        client_info.base_url or "default",
        len(tools),
        len(conversation_messages),
    )

    try:
        response = client.responses.create(
            model=settings.llm_model,
            input=request_input,
            tools=tools,
        )
    except Exception as exc:
        logger.exception(
            "LLM tool request failed provider=%s model=%s base_url=%s exception_type=%s exception_message=%s",
            client_info.provider,
            client_info.model,
            client_info.base_url or "default",
            type(exc).__name__,
            str(exc),
        )
        raise ToolCallCompatibilityError(
            f"Provider rejected the tool-call request. [{type(exc).__name__}: {exc}]",
        ) from exc

    tool_calls = _extract_tool_calls(response)
    output_text = _extract_response_text(response)

    if tool_calls:
        response_id = getattr(response, "id", None)
        if not response_id:
            raise ToolCallCompatibilityError("Provider returned tool calls without a response id.")
        return ToolCallDecision(
            assistant_content=None,
            response_id=str(response_id),
            tool_calls=tool_calls,
        )

    if output_text:
        return ToolCallDecision(
            assistant_content=output_text,
            response_id=getattr(response, "id", None),
            tool_calls=[],
        )

    if _has_unknown_output_items(response):
        logger.error(
            "LLM tool response compatibility failed provider=%s model=%s base_url=%s raw_response=%s",
            client_info.provider,
            client_info.model,
            client_info.base_url or "default",
            _safe_response_preview(response),
        )
        raise ToolCallCompatibilityError(
            "Provider returned unsupported Responses API output items.",
        )

    logger.error(
        "LLM tool response parsing failed provider=%s model=%s base_url=%s raw_response=%s",
        client_info.provider,
        client_info.model,
        client_info.base_url or "default",
        _safe_response_preview(response),
    )
    raise LLMResponseError("The provider returned an empty assistant response.")


def generate_assistant_reply_from_tool_results(
    *,
    previous_response_id: str,
    tool_results: list[dict[str, str]],
    user_message_content: str,
) -> str:
    settings = get_settings()
    client_info = get_llm_client()

    if not client_info.is_configured:
        raise LLMConfigurationError("LLM_API_KEY is not configured.")

    client = _build_openai_client(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )

    logger.info(
        "LLM tool final request starting provider=%s model=%s base_url=%s tool_result_count=%s",
        client_info.provider,
        client_info.model,
        client_info.base_url or "default",
        len(tool_results),
    )

    try:
        response = _create_tool_final_response(
            client=client,
            model=settings.llm_model,
            provider=client_info.provider,
            previous_response_id=previous_response_id,
            tool_results=tool_results,
            user_message_content=user_message_content,
        )
    except Exception as exc:
        logger.exception(
            "LLM tool final request rejected provider=%s model=%s base_url=%s exception_type=%s exception_message=%s",
            client_info.provider,
            client_info.model,
            client_info.base_url or "default",
            type(exc).__name__,
            str(exc),
        )
        raise ToolCallCompatibilityError(
            f"Provider rejected the post-tool message format. [{type(exc).__name__}: {exc}]",
        ) from exc

    logger.info(
        "LLM tool final response received provider=%s model=%s base_url=%s response_shape=%s",
        client_info.provider,
        client_info.model,
        client_info.base_url or "default",
        _response_shape_summary(response),
    )

    output_text = _extract_response_text(response)
    if not output_text:
        logger.error(
            "LLM tool final response parsing failed provider=%s model=%s base_url=%s raw_response=%s",
            client_info.provider,
            client_info.model,
            client_info.base_url or "default",
            _safe_response_preview(response),
        )
        raise LLMResponseError("The provider returned an empty assistant response after tool execution.")

    if not _has_output_text(response):
        logger.info(
            "LLM tool final response extracted text from nested response fields provider=%s model=%s base_url=%s response_shape=%s",
            client_info.provider,
            client_info.model,
            client_info.base_url or "default",
            _response_shape_summary(response),
        )

    return output_text


def _create_tool_final_response(
    *,
    client: OpenAI,
    model: str,
    provider: str,
    previous_response_id: str,
    tool_results: list[dict[str, str]],
    user_message_content: str,
) -> object:
    if provider.lower() == "dashscope":
        logger.info(
            "LLM tool final request using DashScope trusted-context fallback format tool_result_count=%s",
            len(tool_results),
        )
        return client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": _build_trusted_tool_context(tool_results),
                },
                {
                    "role": "user",
                    "content": user_message_content,
                },
            ],
        )

    return client.responses.create(
        model=model,
        previous_response_id=previous_response_id,
        input=[
            {
                "type": "function_call_output",
                "call_id": result["call_id"],
                "output": result["output"],
            }
            for result in tool_results
        ],
    )


def _build_trusted_tool_context(tool_results: list[dict[str, str]]) -> str:
    sections = [
        "Trusted internal tool results are provided below.",
        "Use these results to answer the user's request. Do not claim tool results that are not shown.",
    ]
    for index, result in enumerate(tool_results, start=1):
        sections.extend(
            [
                "",
                f"Tool result {index}: {result['tool_name']}",
                _truncate_tool_context(result["output"]),
            ],
        )
    return "\n".join(sections)


def _truncate_tool_context(value: str) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= 1600:
        return normalized
    return f"{normalized[:1597]}..."


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


def _build_request_input(
    *,
    conversation_messages: list[dict[str, str]],
    system_messages: list[str] | None,
) -> list[dict[str, str]]:
    return [
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


def _extract_tool_calls(response: object) -> list[ToolCallRequest]:
    calls: list[ToolCallRequest] = []
    for item in _as_list(getattr(response, "output", None)):
        item_type = _get_response_item_value(item, "type")
        if item_type != "function_call":
            continue

        call_id = _get_response_item_value(item, "call_id")
        name = _get_response_item_value(item, "name")
        arguments_json = _get_response_item_value(item, "arguments") or "{}"

        if not call_id or not name:
            raise ToolCallCompatibilityError("Provider returned a malformed function_call item.")

        try:
            arguments = json.loads(str(arguments_json))
        except json.JSONDecodeError as exc:
            raise ToolCallCompatibilityError("Provider returned invalid tool arguments JSON.") from exc

        if not isinstance(arguments, dict):
            raise ToolCallCompatibilityError("Provider returned non-object tool arguments.")

        calls.append(
            ToolCallRequest(
                call_id=str(call_id),
                name=str(name),
                arguments=arguments,
                arguments_json=str(arguments_json),
            ),
        )
    return calls


def _get_response_item_value(item: object, key: str) -> object:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def _has_unknown_output_items(response: object) -> bool:
    return any(
        _get_response_item_value(item, "type") not in {"message", "function_call"}
        for item in _as_list(getattr(response, "output", None))
    )


def _extract_response_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    text_parts: list[str] = []
    for item in _as_list(getattr(response, "output", None)):
        content = _get_response_item_value(item, "content")
        if isinstance(content, str) and content.strip():
            text_parts.append(content.strip())
            continue

        for content_item in _as_list(content):
            text = _get_response_item_value(content_item, "text")
            if isinstance(text, str) and text.strip():
                text_parts.append(text.strip())
                continue

            nested_content = _get_response_item_value(content_item, "content")
            if isinstance(nested_content, str) and nested_content.strip():
                text_parts.append(nested_content.strip())

    choices = _as_list(getattr(response, "choices", None))
    for choice in choices:
        message = _get_response_item_value(choice, "message")
        if message is None:
            continue
        content = _get_response_item_value(message, "content")
        if isinstance(content, str) and content.strip():
            text_parts.append(content.strip())

    return "\n".join(text_parts).strip()


def _has_output_text(response: object) -> bool:
    output_text = getattr(response, "output_text", None)
    return isinstance(output_text, str) and bool(output_text.strip())


def _response_shape_summary(response: object) -> str:
    output = _as_list(getattr(response, "output", None))
    output_item_types = [
        str(_get_response_item_value(item, "type") or "<missing>")
        for item in output
    ]
    content_item_types: list[str] = []
    for item in output:
        content = _get_response_item_value(item, "content")
        if isinstance(content, str):
            content_item_types.append("str")
            continue
        for content_item in _as_list(content):
            content_item_types.append(
                str(_get_response_item_value(content_item, "type") or "<missing>"),
            )

    choices = _as_list(getattr(response, "choices", None))
    return (
        f"response_type={type(response).__name__} "
        f"response_id={getattr(response, 'id', None)} "
        f"output_text_present={_has_output_text(response)} "
        f"output_item_types={output_item_types} "
        f"content_item_types={content_item_types} "
        f"choice_count={len(choices)}"
    )


def _safe_response_preview(response: object) -> str:
    try:
        if hasattr(response, "model_dump"):
            return str(response.model_dump())
        if hasattr(response, "__dict__"):
            return str(vars(response))
        return str(response)
    except Exception as exc:
        return f"<unserializable response: {type(exc).__name__}: {exc}>"


def _as_list(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]
