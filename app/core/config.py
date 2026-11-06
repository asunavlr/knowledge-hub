from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/knowledgehub"
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"
    embedding_dimensions: int = Field(default=1536, gt=0)
    chunk_size: int = Field(default=1000, gt=0)
    chunk_overlap: int = Field(default=150, ge=0)
    max_upload_bytes: int = Field(default=20971520, gt=0)
    default_top_k: int = Field(default=5, gt=0, le=20)

@lru_cache
def get_settings() -> Settings:
    return Settings()
