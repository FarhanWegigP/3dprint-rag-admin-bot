"""FastAPI app exposing /health, /ingest, and /chat."""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.api.dashboard import render_dashboard
from app.api.schemas import (
    BotOnlySessionResponse,
    ChatRequest,
    ChatResponse,
    HumanReplyRequest,
    IngestResponse,
    ResumeRequest,
)
from app.config import get_settings
from app.history import (
    append_message,
    ensure_session,
    get_recent_history,
    is_session_paused,
    list_bot_only_sessions,
    list_sessions_overview,
    log_human_reply,
    log_unanswered,
    set_session_paused,
)
from app.ingestion.ingest import run_ingestion
from app.llm import FALLBACK_PHRASE, generate_reply
from app.retrieval.retriever import retrieve

logger = logging.getLogger("threed_bot")

app = FastAPI(title="3D Printing RAG Admin Bot")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
def ingest() -> IngestResponse:
    """Re-run the ingestion pipeline (e.g. after editing 02_faq_index_rag.md)."""
    try:
        run_ingestion()
    except Exception as exc:  # noqa: BLE001 - surface ingestion failures to the caller
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return IngestResponse(status="ok")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    ensure_session(request.session_id, customer_phone=request.customer_phone)

    if is_session_paused(request.session_id):
        # An admin is handling this chat manually — keep the customer's message in history
        # for context, but don't generate or send a bot reply.
        append_message(request.session_id, "user", request.message)
        return ChatResponse(reply=None, session_id=request.session_id, handoff=False, bot_active=False)

    history = get_recent_history(request.session_id)

    chunks = retrieve(request.message)
    top_score = chunks[0].score if chunks else None

    if not chunks or top_score < settings.retrieval_score_threshold:
        reply = FALLBACK_PHRASE
        log_unanswered(request.session_id, request.message, top_score, reason="low_retrieval_score")
        handoff = True
    else:
        result = generate_reply(request.message, chunks, history)
        reply = result.reply
        handoff = result.is_fallback
        if handoff:
            log_unanswered(request.session_id, request.message, top_score, reason="llm_fallback")

    append_message(request.session_id, "user", request.message)
    append_message(request.session_id, "assistant", reply)

    return ChatResponse(reply=reply, session_id=request.session_id, handoff=handoff, bot_active=True)


@app.post("/human-reply")
def human_reply(request: HumanReplyRequest) -> dict[str, str]:
    """Called by the WA gateway when a real admin replies manually from their own phone."""
    log_human_reply(request.session_id, request.message)
    return {"status": "ok"}


@app.get("/handoff/pending", response_model=list[BotOnlySessionResponse])
def handoff_pending() -> list[BotOnlySessionResponse]:
    """Sessions still handled by the bot alone — no human admin has replied yet."""
    return [
        BotOnlySessionResponse(
            session_id=s.session_id, updated_at=s.updated_at, message_count=s.message_count
        )
        for s in list_bot_only_sessions()
    ]


@app.post("/handoff/resume")
def resume(request: ResumeRequest) -> dict[str, str]:
    """Un-pause a session — the bot resumes auto-replying (e.g. admin typed the resume keyword)."""
    set_session_paused(request.session_id, False)
    return {"status": "ok"}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    """Read-only overview of every chat session's status — no more manual SQL queries."""
    return render_dashboard(list_sessions_overview())
