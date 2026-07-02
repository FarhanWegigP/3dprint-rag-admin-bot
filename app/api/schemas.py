"""Request/response models for the FastAPI endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    customer_phone: str | None = None


class ChatResponse(BaseModel):
    reply: str | None
    session_id: str
    handoff: bool
    bot_active: bool


class IngestResponse(BaseModel):
    status: str


class HumanReplyRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class BotOnlySessionResponse(BaseModel):
    session_id: str
    updated_at: str
    message_count: int


class ResumeRequest(BaseModel):
    session_id: str = Field(min_length=1)
