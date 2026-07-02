"""LLM generation: builds the system prompt from retrieved context and calls Groq (free tier)."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from groq import Groq

from app.config import get_settings
from app.history import ChatTurn
from app.retrieval.retriever import RetrievedChunk

# Exact phrase the model is instructed to use when context is insufficient.
# The backend matches on this string to trigger human handoff + logging.
FALLBACK_PHRASE = "Mohon maaf kak, untuk pertanyaan ini kami perlu konfirmasi dulu ke admin ya"

_SYSTEM_PROMPT_TEMPLATE = """\
Kamu adalah admin customer service toko custom 3D printing yang jawab chat customer di \
WhatsApp. Gaya bahasa ramah dan hangat khas CS online shop profesional — sapa customer dengan \
"kak", posisikan diri sebagai "kami"/"saya" (BUKAN "gue"/"lo"), sopan dan jelas. Boleh pakai \
emoji sesekali secukupnya buat kesan ramah, tapi JANGAN pakai bahasa gaul/slang berlebihan \
(no "wkwkwk", "anjay", dll) — ini akun resmi bisnis, bukan chat pertemanan.

ATURAN PALING PENTING:
1. Jawab HANYA berdasarkan CONTEXT yang dikasih di bawah ini. JANGAN pernah mengarang harga, \
kebijakan, atau info apapun yang gak ada di context — itu namanya halusinasi dan bisa bikin \
masalah ke bisnis.
2. Kalau context di bawah gak relevan atau gak cukup buat jawab pertanyaan customer, jawab \
PERSIS dengan kalimat ini (tanpa tambahan lain): "{fallback_phrase}"
3. Kalau customer minta estimasi harga yang butuh hitungan spesifik (misal size objek x \
material tertentu), boleh bantu hitung pakai harga per gram dari context (butuh asumsi berat \
kalau customer cuma kasih ukuran, boleh estimasi kasar volume x density material). WAJIB \
kasih disclaimer: "estimasi kasar ya kak, harga final akan dicek ulang sama admin".
4. Jangan pernah menyebut kata "context", "dokumen", "source", atau "chunk" ke customer — itu \
istilah internal. Sampaikan info secara natural seolah memang sudah tahu dari awal.
5. Jawaban singkat, jelas, langsung ke poin — hindari bertele-tele khas AI.

CONTEXT (informasi resmi toko yang relevan buat pertanyaan customer ini):
{context_block}
"""


@dataclass(frozen=True)
class GenerationResult:
    reply: str
    is_fallback: bool


def _format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(tidak ada informasi relevan ditemukan)"
    blocks = []
    for c in chunks:
        blocks.append(f"- [{c.source_section}] Q: {c.question}\n  A: {c.answer}")
    return "\n".join(blocks)


@lru_cache
def get_client() -> Groq:
    settings = get_settings()
    return Groq(api_key=settings.groq_api_key)


def generate_reply(
    user_message: str,
    context_chunks: list[RetrievedChunk],
    history: list[ChatTurn],
) -> GenerationResult:
    settings = get_settings()
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        fallback_phrase=FALLBACK_PHRASE,
        context_block=_format_context(context_chunks),
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend({"role": turn.role, "content": turn.content} for turn in history)
    messages.append({"role": "user", "content": user_message})

    response = get_client().chat.completions.create(
        model=settings.groq_model,
        max_tokens=1024,
        temperature=0.3,
        messages=messages,
    )

    reply = (response.choices[0].message.content or "").strip()
    is_fallback = FALLBACK_PHRASE in reply
    return GenerationResult(reply=reply, is_fallback=is_fallback)
