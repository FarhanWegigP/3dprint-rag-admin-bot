"""Postgres + pgvector connection pool, shared by the API and ingestion CLI."""
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

import psycopg
from psycopg import Connection
from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector

from app.config import get_settings


def _ensure_vector_extension(conninfo: str) -> None:
    """Create the pgvector extension via a plain connection, before any pooled
    connection tries to register the `vector` type (which fails if it doesn't exist yet)."""
    with psycopg.connect(conninfo, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")


def _configure(conn: Connection) -> None:
    register_vector(conn)


@lru_cache
def get_pool() -> ConnectionPool:
    settings = get_settings()
    _ensure_vector_extension(settings.database_url)
    return ConnectionPool(
        conninfo=settings.database_url,
        min_size=1,
        max_size=10,
        configure=_configure,
        open=True,
    )


@contextmanager
def get_connection() -> Iterator[Connection]:
    with get_pool().connection() as conn:
        yield conn


def close_pool() -> None:
    """Close the pool explicitly. Call at the end of short-lived CLI scripts
    (migrate, ingest) to avoid a harmless but noisy thread-join error at interpreter exit."""
    if get_pool.cache_info().currsize:
        get_pool().close()
