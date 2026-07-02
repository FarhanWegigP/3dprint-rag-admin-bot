-- Migration: initial schema for the 3D-printing RAG bot.
-- Run via: python -m app.db.migrate

CREATE EXTENSION IF NOT EXISTS vector;

-- bge-m3 dense embeddings are 1024-dim.
CREATE TABLE IF NOT EXISTS faq_chunks (
    chunk_id        TEXT PRIMARY KEY,
    question        TEXT NOT NULL,
    answer          TEXT NOT NULL,
    source_section  TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    embedding       VECTOR(1024) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS faq_chunks_embedding_idx
    ON faq_chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id      TEXT PRIMARY KEY,
    -- true while a human admin is manually handling this chat — the bot stays silent for it.
    paused          BOOLEAN NOT NULL DEFAULT false,
    -- Customer's real phone number (E.164-ish, no "+"), resolved by the WA gateway. session_id
    -- itself may be a privacy "@lid" ID rather than the phone number, so this can be NULL.
    customer_phone  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Safe to re-run: adds the column on a database migrated before this field existed.
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS paused BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS customer_phone TEXT;

CREATE TABLE IF NOT EXISTS chat_messages (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    -- true when a human admin sent this from their own phone/WhatsApp (not the bot).
    is_human    BOOLEAN NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Safe to re-run: adds the column on a database migrated before this field existed.
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS is_human BOOLEAN NOT NULL DEFAULT false;

CREATE INDEX IF NOT EXISTS chat_messages_session_idx
    ON chat_messages (session_id, created_at);

-- Questions the bot couldn't answer confidently — reviewed later to grow the KB.
CREATE TABLE IF NOT EXISTS unanswered_queries (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT,
    query       TEXT NOT NULL,
    top_score   DOUBLE PRECISION,
    reason      TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
