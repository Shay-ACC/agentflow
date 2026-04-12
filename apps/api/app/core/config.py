from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = Field(default="AgentFlow", alias="PROJECT_NAME")
    project_env: str = Field(default="development", alias="PROJECT_ENV")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    database_url: str = Field(
        default="postgresql+psycopg://agentflow:agentflow@localhost:5432/agentflow",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4.1-mini", alias="LLM_MODEL")
    llm_base_url: str | None = Field(default=None, alias="LLM_BASE_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
