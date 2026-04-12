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
    embedding_provider: str = Field(default="openai", alias="EMBEDDING_PROVIDER")
    embedding_api_key: str = Field(default="", alias="EMBEDDING_API_KEY")
    embedding_model: str = Field(default="", alias="EMBEDDING_MODEL")
    embedding_base_url: str | None = Field(default=None, alias="EMBEDDING_BASE_URL")
    qdrant_collection_name: str = Field(
        default="document_chunks",
        alias="QDRANT_COLLECTION_NAME",
    )
    rag_top_k: int = Field(default=3, alias="RAG_TOP_K")
    rag_chunk_size: int = Field(default=900, alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=180, alias="RAG_CHUNK_OVERLAP")


@lru_cache
def get_settings() -> Settings:
    return Settings()
