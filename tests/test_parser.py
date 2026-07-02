"""Self-check for the FAQ parser. Run: python tests/test_parser.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.parser import parse_faq_markdown

SAMPLE = """\
# FAQ

[source: Kebijakan Harga]
Q: Berapa harga print per gram?
A: PLA Rp300/gram, PETG Rp350/gram.

[source: Kebijakan Harga]
Q: Ada minimum order?
A: Ada, minimum charge Rp50.000.

[source: Kebijakan Waktu Pengerjaan]
Q: Berapa lama proses print barang kecil?
A: 1-2 hari kerja untuk objek di bawah 10cm.
"""


def test_parse_faq_markdown() -> None:
    chunks = parse_faq_markdown(SAMPLE)
    assert len(chunks) == 3

    assert chunks[0].chunk_id == "kebijakan-harga-001"
    assert chunks[0].source_section == "Kebijakan Harga"
    assert chunks[0].question == "Berapa harga print per gram?"
    assert "PLA Rp300/gram" in chunks[0].answer

    # Second chunk in the same section gets the next running index.
    assert chunks[1].chunk_id == "kebijakan-harga-002"

    # Different section resets its own counter.
    assert chunks[2].chunk_id == "kebijakan-waktu-pengerjaan-001"

    # embedding_text combines question + answer.
    assert chunks[0].question in chunks[0].embedding_text
    assert chunks[0].answer in chunks[0].embedding_text

    # content_hash is stable and changes when content changes.
    reparsed = parse_faq_markdown(SAMPLE)
    assert chunks[0].content_hash == reparsed[0].content_hash

    mutated = SAMPLE.replace("Rp300/gram", "Rp999/gram")
    mutated_chunks = parse_faq_markdown(mutated)
    assert mutated_chunks[0].content_hash != chunks[0].content_hash
    assert mutated_chunks[0].chunk_id == chunks[0].chunk_id  # idempotent upsert key unchanged


def test_parse_real_kb_file() -> None:
    kb_path = Path(__file__).resolve().parent.parent / "data/knowledge_base/02_faq_index_rag.md"
    chunks = parse_faq_markdown(kb_path.read_text(encoding="utf-8"))
    assert len(chunks) > 0
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "chunk_ids must be unique"


if __name__ == "__main__":
    test_parse_faq_markdown()
    test_parse_real_kb_file()
    print("OK - all parser checks passed")
