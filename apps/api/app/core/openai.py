from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True)
class OpenAIClientPlaceholder:
    api_key: str

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key) and self.api_key != "your_openai_api_key_here"


def get_openai_client() -> OpenAIClientPlaceholder:
    settings = get_settings()
    return OpenAIClientPlaceholder(api_key=settings.openai_api_key)
