"""Ingestion command: parse the FAQ markdown, embed each chunk, and upsert into pgvector.

Idempotent — re-running after editing 02_faq_index_rag.md only writes chunks whose
content_hash changed, and removes chunks that no longer exist in the file.

Usage:
    python -m app.ingestion.ingest
"""
from __future__ import annotations

from app.config import get_settings
from app.db.connection import close_pool, get_connection
from app.ingestion.embedder import embed_texts
from app.ingestion.parser import parse_faq_file

_UPSERT_SQL = """
INSERT INTO faq_chunks (chunk_id, question, answer, source_section, content_hash, embedding)
VALUES (%(chunk_id)s, %(question)s, %(answer)s, %(source_section)s, %(content_hash)s, %(embedding)s::vector)
ON CONFLICT (chunk_id) DO UPDATE SET
    question = EXCLUDED.question,
    answer = EXCLUDED.answer,
    source_section = EXCLUDED.source_section,
    content_hash = EXCLUDED.content_hash,
    embedding = EXCLUDED.embedding,
    updated_at = now()
WHERE faq_chunks.content_hash IS DISTINCT FROM EXCLUDED.content_hash
"""


def run_ingestion() -> None:
    settings = get_settings()
    chunks = parse_faq_file(settings.kb_faq_path)
    if not chunks:
        print(f"No Q&A chunks found in {settings.kb_faq_path}")
        return

    embeddings = embed_texts([c.embedding_text for c in chunks])

    with get_connection() as conn:
        with conn.cursor() as cur:
            for chunk, embedding in zip(chunks, embeddings):
                cur.execute(
                    _UPSERT_SQL,
                    {
                        "chunk_id": chunk.chunk_id,
                        "question": chunk.question,
                        "answer": chunk.answer,
                        "source_section": chunk.source_section,
                        "content_hash": chunk.content_hash,
                        "embedding": embedding,
                    },
                )

            current_ids = tuple(c.chunk_id for c in chunks)
            deleted = cur.execute(
                "DELETE FROM faq_chunks WHERE chunk_id != ALL(%s)",
                (list(current_ids),),
            ).rowcount

        conn.commit()

    print(f"Ingested {len(chunks)} chunks from {settings.kb_faq_path} (removed {deleted} stale chunks)")


if __name__ == "__main__":
    run_ingestion()
    close_pool()
