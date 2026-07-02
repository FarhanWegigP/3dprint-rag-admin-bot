# Bot Admin WA — Custom 3D Printing (RAG)

Bot admin WhatsApp yang jawab pertanyaan customer (harga, waktu pengerjaan, ukuran, material,
dll) pakai RAG: retrieval dari `data/knowledge_base/` + generation via Groq (LLM gratis). Jawaban selalu
digrounding ke knowledge base — kalau gak ada info relevan, bot jujur bilang belum tau dan
handoff ke admin manusia (dicatat di tabel `unanswered_queries`).

Status: poin 1-3 (ingestion, retrieval, generation) sudah jalan dan bisa ditest via `/chat`.
WA gateway (poin 4, folder `wa-gateway/`) menyusul setelah backend ditest.

## Struktur project

```
data/knowledge_base/   SOP (source of truth) + FAQ turunan buat RAG
app/ingestion/         parser Q&A + embedding (bge-m3) + upsert ke pgvector
app/retrieval/         vector search + CrossEncoder rerank
app/api/                FastAPI: /health, /ingest, /chat
app/db/                 schema.sql + migration runner + connection pool
app/llm.py              system prompt + panggil Groq
app/history.py          history percakapan per session_id
wa-gateway/             Node whatsapp-web.js (belum diimplementasi)
```

## 1. Setup dari nol

### Prasyarat
- Python 3.11+
- PostgreSQL 14+ dengan extension `pgvector` ter-install (atau pakai Docker, lihat di bawah)
- API key Groq (gratis) — daftar di https://console.groq.com/keys, tinggal login pake Google/GitHub

**Gak punya Postgres lokal? Pakai Docker:**

```bash
docker run -d --name threed-bot-pg \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=threed_bot \
  -p 5432:5432 pgvector/pgvector:pg16
```

Extension `vector` udah dibuat otomatis sama app (lihat `app/db/connection.py`), gak perlu
`CREATE EXTENSION` manual.

### Install

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
```

Buka `.env`, isi minimal 2 hal ini:

```
DATABASE_URL=postgresql://user:pass@localhost:5432/threed_bot
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx     <- taro API key Groq lo di sini
```

**Taro API key-nya di file `.env`** (bukan `.env.example`, dan bukan di-hardcode di kode).
File `.env` ini di-`.gitignore` biar gak kecommit — jangan pernah push API key ke git.

Model embedding (`BAAI/bge-m3`, ~2.2GB) dan reranker (default `BAAI/bge-reranker-base`, ~1.1GB)
di-download otomatis dari HuggingFace saat pertama kali dipanggil (butuh koneksi internet sekali
di awal, lalu ke-cache lokal di `~/.cache/huggingface`).

> **Disk cekak / Windows "paging file too small"?** Kalau drive tempat home directory-nya mepet,
> pindahin cache HuggingFace ke drive lain: set env var `HF_HOME=D:\hf-cache\huggingface` (atau
> `export HF_HOME=/path/lain` di Linux/Mac) sebelum jalanin apapun yang muat model. Kalau muncul
> error `OSError: paging file too small` pas load reranker, itu bukan soal disk lagi tapi limit
> virtual memory Windows saat mmap model gede — pakai reranker yang lebih kecil
> (`RERANKER_MODEL_NAME=BAAI/bge-reranker-base`, default-nya emang ini) atau naikin ukuran
> pagefile Windows.

### Migration

Pastikan database sudah ada dan extension `vector` bisa di-load (`CREATE EXTENSION vector`
butuh pgvector ter-install di server Postgres-nya, bukan cuma di client).

```bash
python -m app.db.migrate
```

Ini bikin tabel `faq_chunks`, `chat_sessions`, `chat_messages`, `unanswered_queries`.

### Ingest knowledge base

```bash
python -m app.ingestion.ingest
```

Parse `data/knowledge_base/02_faq_index_rag.md`, generate embedding tiap chunk, upsert ke
`faq_chunks`. **Idempotent** — jalanin ulang gak bikin duplikat (upsert by `chunk_id`, cuma
nulis ulang row yang `content_hash`-nya berubah), dan chunk yang udah dihapus dari file bakal
ikut kehapus dari DB.

### Jalanin backend

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

## 2. Test via curl

```bash
curl -s http://localhost:8000/health

curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "kak harga print per gram berapa ya?", "session_id": "628123456789"}'

# Lanjutan (kontekstual, pake session_id yang sama)
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "kalau pake PETG gimana?", "session_id": "628123456789"}'

# Pertanyaan di luar knowledge base -> harus fallback + kecatat di unanswered_queries
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "kalian terima pembayaran pake bitcoin gak?", "session_id": "628123456789"}'
```

Response shape:

```json
{"reply": "...", "session_id": "628123456789", "handoff": false}
```

`handoff: true` artinya bot gak yakin (retrieval score di bawah threshold atau LLM eksplisit
bilang gak tau) — pertanyaannya udah otomatis kecatat di tabel `unanswered_queries` buat
direview dan ditambahin ke knowledge base.

## 3. Re-ingest kalau SOP/FAQ di-update

Alurnya: edit `01_SOP_kebijakan_3dprinting.md` (source of truth) -> generate ulang
`02_faq_index_rag.md` (Q&A per chunk, tiap chunk ada tag `[source: <section>]`) -> jalanin:

```bash
python -m app.ingestion.ingest
# atau lewat endpoint:
curl -X POST http://localhost:8000/ingest
```

Ini otomatis update chunk yang berubah, tambah chunk baru, dan hapus chunk yang udah gak ada
di file — tanpa duplikat.

## 4. WA Gateway (belum diimplementasi)

`wa-gateway/` bakal isi service Node pakai `whatsapp-web.js`: terima pesan WA masuk, forward
ke `POST /chat`, kirim balik jawabannya, dengan QR login, auto-reconnect, dan debounce biar
gak spam-reply kalau customer kirim banyak pesan beruntun. Dikerjain setelah backend ini
ditest dan stabil.

## Catatan implementasi

- Embedding = gabungan `question + answer` (bukan cuma pertanyaan) biar capture konteks
  lengkap saat di-embed.
- Retrieval: pgvector cosine top-10 kandidat -> CrossEncoder rerank -> top-4 final
  (`RETRIEVAL_TOP_K_CANDIDATES` / `RETRIEVAL_TOP_K_FINAL` di `.env`).
- Kalau skor retrieval di bawah `RETRIEVAL_SCORE_THRESHOLD`, bot langsung fallback tanpa
  manggil LLM sama sekali (hemat biaya + hindari halusinasi).
- LLM diinstruksikan jawab HANYA dari context yang di-retrieve, dan wajib pakai kalimat baku
  tertentu kalau gak ada info relevan — backend cocokin kalimat itu buat nge-trigger handoff
  + logging, bukan nebak-nebak dari isi jawaban.
