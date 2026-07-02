"""Retrieval: embed query -> pgvector top-k -> CrossEncoder rerank -> top final chunks."""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.config import get_settings
from app.db.connection import get_connection
from app.ingestion.embedder import embed_query

_SEARCH_SQL = """
SELECT chunk_id, question, answer, source_section,
       1 - (embedding <=> %(query_embedding)s::vector) AS vector_score
FROM faq_chunks
ORDER BY embedding <=> %(query_embedding)s::vector
LIMIT %(top_k)s
"""


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    question: str
    answer: str
    source_section: str
    score: float


@lru_cache
def get_reranker() -> CrossEncoder:
    settings = get_settings()
    return CrossEncoder(settings.reranker_model_name, device=settings.embedding_device)


def _vector_search(query: str, top_k: int) -> list[RetrievedChunk]:
    query_embedding = embed_query(query)
    with get_connection() as conn:
        rows = conn.execute(
            _SEARCH_SQL,
            {"query_embedding": query_embedding, "top_k": top_k},
        ).fetchall()

    return [
        RetrievedChunk(
            chunk_id=row[0],
            question=row[1],
            answer=row[2],
            source_section=row[3],
            score=float(row[4]),
        )
        for row in rows
    ]


def retrieve(query: str, top_k: int | None = None) -> list[RetrievedChunk]:
    """Embed the query, run vector search, rerank with a CrossEncoder, return the final top chunks."""
    settings = get_settings()
    final_k = top_k or settings.retrieval_top_k_final

    candidates = _vector_search(query, settings.retrieval_top_k_candidates)
    if not candidates:
        return []

    reranker = get_reranker()
    pairs = [[query, f"{c.question}\n{c.answer}"] for c in candidates]
    raw_scores = reranker.predict(pairs)
    # bge-reranker-v2-m3 outputs raw logits; squash to [0, 1] so RETRIEVAL_SCORE_THRESHOLD is meaningful.
    rerank_scores = [1 / (1 + math.exp(-float(s))) for s in raw_scores]

    reranked = sorted(
        (
            RetrievedChunk(c.chunk_id, c.question, c.answer, c.source_section, score)
            for c, score in zip(candidates, rerank_scores)
        ),
        key=lambda c: c.score,
        reverse=True,
    )

    return reranked[:final_k]
