"""Central app configuration. All tunables come from environment variables (.env) — no magic strings."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str

    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    embedding_model_name: str = "BAAI/bge-m3"
    reranker_model_name: str = "BAAI/bge-reranker-base"
    embedding_device: str = "cpu"

    kb_faq_path: str = "data/knowledge_base/02_faq_index_rag.md"

    retrieval_top_k_candidates: int = 10
    retrieval_top_k_final: int = 4
    retrieval_score_threshold: float = 0.35

    history_max_turns: int = 8

    api_host: str = "0.0.0.0"
    api_port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
