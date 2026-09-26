# Architecture

## 1. High-level shape

```
┌───────────────────────────┐        HTTP/JSON        ┌─────────────────────────────┐
│  React SPA (Vite + TS)    │  ───────────────────▶   │  FastAPI (Python)           │
│  - Upload                 │                         │  /api/*                     │
│  - Material / concept     │  ◀───────────────────   │                             │
│  - Lesson view            │                         │  Services:                  │
│  - Quiz runner            │                         │   ingestion → structuring   │
│  - Study session          │                         │   → teaching → assessment   │
└───────────────────────────┘                         │   → adaptive                │
                                                      │                             │
                                                      │  LLM Layer (interface):     │
                                                      │   openai|anthropic|ollama   │
                                                      │                             │
                                                      │  SQLite (SQLAlchemy)        │
                                                      │  Local chunk/vector store   │
                                                      └─────────────────────────────┘
```

## 2. Why this shape

- **Monorepo, two runtimes.** `backend/` and `frontend/` are independently runnable.
  The SPA talks only to the API — no server-side rendering lock-in.
- **Service layer owns the pipeline.** API routes are thin; each of the five
  capabilities is a service with a single responsibility, making the adaptive logic
  testable without HTTP or an LLM.
- **LLM interface is the seam.** Everything AI-related goes through
  `llm/base.py`. Adding a provider means adding one file, not touching services.

## 3. Request lifecycle: processing a material

```
POST /api/materials/{id}/process
        │
        ▼
[ingestion]  extract text → clean → chunk → embed → store chunks
        │
        ▼
[structuring] LLM: chunks → concept graph (title, summary, order, parent)
        │
        ▼
[teaching]   for each concept: retrieve chunks → LLM → lesson content
        │
        ▼
   material.status = "ready"
```

This is synchronous in the MVP (FastAPI `BackgroundTasks` optional). The
`material.status` field (`uploaded → processing → ready | failed`) is the contract
the frontend polls, so moving to a real worker (Celery/RQ) later is transparent.

## 4. Request lifecycle: adaptive study step

```
POST /api/sessions/{id}/next
        │
        ▼
[adaptive] read mastery per concept → apply policy:
              mastery < 0.4  → RETEACH  (regenerate simpler lesson)
              0.4–0.8        → PRACTICE (generate more questions)
              > 0.8          → ADVANCE  (next concept)
        │
        ▼
   returns an Action { type, concept, lesson_id?, quiz? }
```

## 5. Provider-agnostic LLM layer

```
llm/
  base.py            LLMProvider (ABC): complete(), generate_json(), embed()
  factory.py         get_llm() reads settings.LLM_PROVIDER
  openai_provider.py
  anthropic_provider.py
  ollama_provider.py
```

- `complete()` — plain text completion.
- `generate_json()` — completion constrained to JSON + robust parsing/repair.
- `embed()` — text → vectors, used for retrieval grounding.

Embeddings may come from a *different* provider than generation
(`EMBEDDING_PROVIDER`), e.g. Anthropic for generation + Ollama for embeddings.

## 6. Data & retrieval (MVP)

- **SQLite** via SQLAlchemy 2.0, models in `app/models.py`.
- **Chunks + embeddings** stored in a `chunks` table; vectors serialized as JSON.
- **Retrieval** is in-process cosine similarity in pure Python (no heavy native
  deps). For MVP-scale material this is fast and removes the need for a separate
  vector DB.
- Migration path: `chunks.embedding` → pgvector column; retrieval swaps behind the
  same `retrieve(material_id, query, k)` function.

## 7. Configuration

All via environment variables (`.env`), loaded in `app/config.py`:

| Var | Purpose | Default |
|---|---|---|
| `LLM_PROVIDER` | generation backend | `ollama` |
| `EMBEDDING_PROVIDER` | embedding backend | `ollama` |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | credentials | empty |
| `OLLAMA_BASE_URL` | local inference | `http://localhost:11434` |
| `LLM_MODEL` / `EMBEDDING_MODEL` | model names | provider-specific |
| `DATABASE_URL` | DB | `sqlite:///./suhail.db` |
| `CORS_ORIGINS` | frontend origin | `http://localhost:5173` |

## 8. Failure & robustness

- Provider errors raise `LLMError`; routes return `502` with a readable message.
- `generate_json()` retries once with a "return only valid JSON" repair prompt.
- If embedding fails during processing, the material is still structured using
  full-text chunks (retrieval degrades, pipeline continues).
- Every long step updates `material.status` / `lesson.status` so failures are visible.

## 9. Future architecture (post-MVP)

- Auth + tenancy (JWT / OAuth), roles for teacher/student.
- Background worker queue for processing.
- Postgres + pgvector.
- Spaced-repetition scheduler layered on the mastery model.
- Streaming lesson generation (SSE) for perceived speed.
