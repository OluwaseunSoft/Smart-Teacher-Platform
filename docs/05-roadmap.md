# Roadmap

## Phase 0 — Design & scaffold  ← **this session**
- [x] Product overview, architecture, data model, API spec, AI pipeline docs.
- [x] FastAPI backend scaffold with models, schemas, routes, stub services.
- [x] Provider-agnostic LLM layer (OpenAI / Anthropic / Ollama).
- [x] React + Vite + TS SPA scaffold with the core-loop pages.

## Phase 1 — Working core loop (single-user)
- [ ] File upload (PDF/TXT) + paste-text ingestion end to end.
- [ ] Real structuring, teaching, assessment, and adaptive implementations
      validated against a real provider.
- [ ] Mastery persistence and `next` action policy.
- [ ] Basic error/empty/loading states across the UI.
- [ ] Backend tests for `adaptive` and `assessment` grading (no LLM needed).

## Phase 2 — Learning quality
- [ ] Streaming lesson generation (SSE) for perceived speed.
- [ ] Spaced-repetition scheduler on top of mastery.
- [ ] Richer question types (multi-select, ordering, cloze).
- [ ] Student-selectable learning style / explanation depth.
- [ ] Source citations rendered in lessons (chunk references).

## Phase 3 — Accounts & multi-user
- [ ] Auth (email + OAuth), student/teacher roles.
- [ ] Per-student data isolation; teacher assignment of materials.
- [ ] Postgres + pgvector; migrate the chunk store.
- [ ] Background worker (Celery/RQ) for processing.

## Phase 4 — Product & scale
- [ ] Progress dashboards, streaks, study plans.
- [ ] Notifications and reminders.
- [ ] Cost/observability dashboards per provider.
- [ ] Content export (PDF study guides).

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Hallucinated lesson content | Ground in retrieved chunks; show citations (Phase 2). |
| Provider outages / rate limits | Provider abstraction + Ollama fallback. |
| Poor PDF text extraction | Clear failure state; prompt user to paste text. |
| Infinite "reteach" loops | Attempts cap per concept, then force advance with flag. |
| Cost blowup | top-k retrieval, token caps, structuring once. |

## Definition of done (MVP)

A single user can upload material, get structured lessons, take quizzes, and be
guided by an adaptive next-step engine — locally, with the AI provider switchable by
env var alone.
