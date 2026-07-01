from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "sqlite:///./feedback.db"
    dify_base_url: str = "http://host.docker.internal:18080/v1"
    dify_feedback_workflow_api_key: str = ""
    dify_timeout_seconds: float = 20.0
    workflow_version: str = "feedback-structuring-v1"
    allow_demo_analyzer: bool = True
    demo_session_ttl_hours: int = 24
    live_session_daily_limit: int = 5
    live_global_daily_limit: int = 100
    max_message_chars: int = 2_000
    max_csv_rows: int = 10
    max_csv_bytes: int = 1_000_000
    embedding_model: str = "BAAI/bge-small-zh-v1.5"


@lru_cache
def get_settings() -> Settings:
    return Settings()

