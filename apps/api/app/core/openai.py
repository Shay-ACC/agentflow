import logging
from dataclasses import dataclass

from openai import OpenAI

from app.core.config import Settings, get_settings


logger = logging.getLogger(__name__)


class LLMConfigurationError(Exception):
    pass


class LLMResponseError(Exception):
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


def get_llm_client() -> LLMClientInfo:
    settings = get_settings()
    return LLMClientInfo(
        provider=settings.llm_provider,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
    )


def generate_assistant_reply(
    *,
    conversation_messages: list[dict[str, str]],
) -> str:
    settings = get_settings()
    client_info = get_llm_client()

    if not client_info.is_configured:
        raise LLMConfigurationError("LLM_API_KEY is not configured.")

    client = _build_openai_client(settings)
    response = None
    request_input = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in conversation_messages
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


def _build_openai_client(settings: Settings) -> OpenAI:
    client_kwargs: dict[str, str] = {
        "api_key": settings.llm_api_key,
    }
    if settings.llm_base_url:
        client_kwargs["base_url"] = settings.llm_base_url
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
