"""BAAI/bge-m3 embedding wrapper, shared by ingestion and retrieval."""
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import get_settings

EMBEDDING_DIM = 1024


@lru_cache
def get_embedder() -> SentenceTransformer:
    settings = get_settings()
    return SentenceTransformer(settings.embedding_model_name, device=settings.embedding_device)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts, normalized for cosine similarity search."""
    model = get_embedder()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
