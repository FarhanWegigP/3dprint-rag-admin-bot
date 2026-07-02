"""Per-session conversation history, persisted in Postgres."""
from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings
from app.db.connection import get_connection


@dataclass(frozen=True)
class ChatTurn:
    role: str  # "user" | "assistant"
    content: str


@dataclass(frozen=True)
class BotOnlySession:
    """A session that has never had a human admin reply — still handled by the bot alone."""

    session_id: str
    updated_at: str
    message_count: int


@dataclass(frozen=True)
class SessionOverview:
    """One row of the admin dashboard: session status at a glance."""

    session_id: str
    paused: bool
    ever_human: bool
    message_count: int
    last_message: str
    updated_at: str
    customer_phone: str | None


def ensure_session(session_id: str, customer_phone: str | None = None) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_sessions (session_id, customer_phone) VALUES (%s, %s) "
            "ON CONFLICT (session_id) DO UPDATE SET customer_phone = COALESCE(EXCLUDED.customer_phone, chat_sessions.customer_phone)",
            (session_id, customer_phone),
        )
        conn.commit()


def get_recent_history(session_id: str, max_turns: int | None = None) -> list[ChatTurn]:
    """Return the last `max_turns` messages (user+assistant combined) in chronological order."""
    settings = get_settings()
    limit = max_turns or settings.history_max_turns

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM (
                SELECT role, content, created_at FROM chat_messages
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            ) recent
            ORDER BY created_at ASC
            """,
            (session_id, limit),
        ).fetchall()

    return [ChatTurn(role=row[0], content=row[1]) for row in rows]


def append_message(session_id: str, role: str, content: str, is_human: bool = False) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, is_human) VALUES (%s, %s, %s, %s)",
            (session_id, role, content, is_human),
        )
        conn.execute(
            "UPDATE chat_sessions SET updated_at = now() WHERE session_id = %s",
            (session_id,),
        )
        conn.commit()


def log_human_reply(session_id: str, content: str) -> None:
    """Record a message a real admin sent manually from their own phone — also pauses the
    bot for this session, since the admin is now handling it directly."""
    ensure_session(session_id)
    append_message(session_id, "assistant", content, is_human=True)
    set_session_paused(session_id, True)


def is_session_paused(session_id: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT paused FROM chat_sessions WHERE session_id = %s", (session_id,)
        ).fetchone()
    return bool(row[0]) if row else False


def set_session_paused(session_id: str, paused: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE chat_sessions SET paused = %s, updated_at = now() WHERE session_id = %s",
            (paused, session_id),
        )
        conn.commit()


def list_bot_only_sessions() -> list[BotOnlySession]:
    """Sessions where every reply so far came from the bot — no human admin has stepped in yet."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT cs.session_id, cs.updated_at,
                   (SELECT count(*) FROM chat_messages cm WHERE cm.session_id = cs.session_id)
            FROM chat_sessions cs
            WHERE NOT EXISTS (
                SELECT 1 FROM chat_messages cm2
                WHERE cm2.session_id = cs.session_id AND cm2.is_human = true
            )
            ORDER BY cs.updated_at DESC
            """
        ).fetchall()

    return [
        BotOnlySession(session_id=row[0], updated_at=row[1].isoformat(), message_count=row[2])
        for row in rows
    ]


def list_sessions_overview() -> list[SessionOverview]:
    """All sessions with status/activity summary, most recently active first — dashboard data."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                cs.session_id,
                cs.paused,
                EXISTS (
                    SELECT 1 FROM chat_messages cm WHERE cm.session_id = cs.session_id AND cm.is_human = true
                ) AS ever_human,
                (SELECT count(*) FROM chat_messages cm WHERE cm.session_id = cs.session_id) AS message_count,
                (
                    SELECT content FROM chat_messages cm
                    WHERE cm.session_id = cs.session_id
                    ORDER BY created_at DESC LIMIT 1
                ) AS last_message,
                cs.updated_at,
                cs.customer_phone
            FROM chat_sessions cs
            ORDER BY cs.updated_at DESC
            """
        ).fetchall()

    return [
        SessionOverview(
            session_id=row[0],
            paused=row[1],
            ever_human=row[2],
            message_count=row[3],
            last_message=row[4] or "",
            updated_at=row[5].isoformat(),
            customer_phone=row[6],
        )
        for row in rows
    ]


def log_unanswered(session_id: str, query: str, top_score: float | None, reason: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO unanswered_queries (session_id, query, top_score, reason) VALUES (%s, %s, %s, %s)",
            (session_id, query, top_score, reason),
        )
        conn.commit()
