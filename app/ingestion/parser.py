"""Parse 02_faq_index_rag.md into Q&A chunks.

Delimiter is a `[source: <section>]` tag; each chunk runs from one tag up to
(but not including) the next tag.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_SOURCE_TAG_RE = re.compile(r"^\[source:\s*(?P<section>.+?)\]\s*$", re.MULTILINE)
_QA_RE = re.compile(r"Q:\s*(?P<question>.+?)\s*\nA:\s*(?P<answer>.+)", re.DOTALL)


@dataclass(frozen=True)
class FaqChunk:
    chunk_id: str
    question: str
    answer: str
    source_section: str
    content_hash: str

    @property
    def embedding_text(self) -> str:
        """Question + answer combined so the embedding captures full context."""
        return f"{self.question}\n{self.answer}"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def _content_hash(question: str, answer: str, source_section: str) -> str:
    payload = f"{source_section}\x1f{question}\x1f{answer}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_faq_markdown(text: str) -> list[FaqChunk]:
    """Split the FAQ markdown into chunks, one per [source: ...] tag."""
    matches = list(_SOURCE_TAG_RE.finditer(text))
    chunks: list[FaqChunk] = []
    section_counters: dict[str, int] = {}

    for i, match in enumerate(matches):
        section = match.group("section").strip()
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()

        qa_match = _QA_RE.search(body)
        if not qa_match:
            continue

        question = qa_match.group("question").strip()
        answer = qa_match.group("answer").strip()

        section_slug = _slugify(section)
        section_counters[section_slug] = section_counters.get(section_slug, 0) + 1
        chunk_id = f"{section_slug}-{section_counters[section_slug]:03d}"

        chunks.append(
            FaqChunk(
                chunk_id=chunk_id,
                question=question,
                answer=answer,
                source_section=section,
                content_hash=_content_hash(question, answer, section),
            )
        )

    return chunks


def parse_faq_file(path: str) -> list[FaqChunk]:
    with open(path, "r", encoding="utf-8") as f:
        return parse_faq_markdown(f.read())
