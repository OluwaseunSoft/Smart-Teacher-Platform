# API Specification

Base URL: `http://localhost:8000`. All request/response bodies are JSON except file
uploads (`multipart/form-data`). Errors use FastAPI's shape:

```json
{ "detail": "human-readable message" }
```

## Health

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Liveness + configured providers |

```json
{ "status": "ok", "llm_provider": "ollama", "embedding_provider": "ollama" }
```

## Materials

| Method | Path | Description |
|---|---|---|
| POST | `/api/materials` | Upload a file (`file`) or text (`text`, `title`). Creates a Material with `status=uploaded`. |
| GET | `/api/materials` | List materials (newest first). |
| GET | `/api/materials/{id}` | Get one material. |
| POST | `/api/materials/{id}/process` | Run the full pipeline (ingest → structure → teach). Sets `status`. |
| GET | `/api/materials/{id}/concepts` | List concepts in curriculum order. |
| GET | `/api/materials/{id}/lessons` | List lessons (with concept info). |
| DELETE | `/api/materials/{id}` | Delete a material and all dependents. |

**Upload (file):** `multipart/form-data`, field `file` (PDF or `.txt`).
**Upload (text):** `application/json`:

```json
{ "title": "Biology Chapter 3", "text": "..." }
```

Material response:

```json
{
  "id": 1, "title": "Biology Chapter 3", "source_type": "pdf",
  "status": "ready", "error": null, "created_at": "2026-09-22T10:00:00Z"
}
```

## Concepts

| Method | Path | Description |
|---|---|---|
| GET | `/api/concepts/{id}` | Get a concept. |

```json
{ "id": 4, "material_id": 1, "parent_id": null, "title": "Photosynthesis",
  "summary": "...", "order_index": 2, "difficulty": "core" }
```

## Topic study view

| Method | Path | Description |
|---|---|---|
| GET | `/api/curriculum` | List the student's subject → chapter → topic hierarchy. |
| GET | `/api/topics/{id}` | Get topic details, associated lessons, and source excerpts. |

The topic response includes `grounding` references with the source chunk's
`content`, `index`, and `relevance`, plus source material metadata. This endpoint
is scoped to the authenticated student's materials.

## Lessons

| Method | Path | Description |
|---|---|---|
| GET | `/api/lessons/{id}` | Full lesson content. |
| POST | `/api/lessons/{id}/regenerate` | Regenerate lesson (optionally simpler). Body: `{ "simpler": true }`. |
| POST | `/api/lessons/{id}/quiz` | Generate (or return existing) quiz for the lesson. |
| GET | `/api/lessons/{id}/quiz` | Get the quiz for the lesson. |

Lesson response:

```json
{
  "id": 10, "concept_id": 4, "title": "Photosynthesis",
  "objectives": ["State the overall equation", "Explain light reactions"],
  "content": "## Overview\n...", "status": "ready"
}
```

Quiz response (**answers omitted**):

```json
{
  "lesson_id": 10,
  "questions": [
    { "id": 55, "type": "mcq", "prompt": "What is released?",
      "options": ["O2", "CO2", "N2", "CH4"], "difficulty": 2 },
    { "id": 56, "type": "short", "prompt": "Define photolysis.", "difficulty": 3 }
  ]
}
```

> Correct answers are never sent to the client before submission.

## Quizzes & grading

| Method | Path | Description |
|---|---|---|
| POST | `/api/quizzes/{lesson_id}/submit` | Submit answers, grade, update mastery. |

Request:

```json
{ "answers": [ { "question_id": 55, "response": "O2" },
               { "question_id": 56, "response": "splitting of water" } ] }
```

Response:

```json
{
  "lesson_id": 10,
  "score": 0.75,
  "results": [
    { "question_id": 55, "correct": true,  "correct_answer": "O2",
      "explanation": "..." },
    { "question_id": 56, "correct": false, "correct_answer": "The light-driven
      splitting of water...", "explanation": "..." }
  ],
  "concept_mastery": [ { "concept_id": 4, "score": 0.68 } ]
}
```

## Study sessions (adaptive loop)

| Method | Path | Description |
|---|---|---|
| POST | `/api/sessions` | Start a session. Body: `{ "material_id": 1 }`. |
| GET | `/api/sessions/{id}` | Session state + per-concept mastery. |
| POST | `/api/sessions/{id}/next` | Get the next adaptive action. |

`next` response — a discriminated union on `type`:

```json
{ "type": "advance", "concept": { "id": 5, "title": "..." },
  "lesson": { "id": 11, "title": "..." }, "message": "Nice work — moving on." }
```
```json
{ "type": "practice", "concept": { "id": 4, "title": "..." },
  "quiz": { "lesson_id": 10, "questions": [ ... ] },
  "message": "Let's reinforce this with a few more questions." }
```
```json
{ "type": "reteach", "concept": { "id": 4, "title": "..." },
  "lesson": { "id": 12, "title": "..." },
  "message": "Let's revisit this with a different explanation." }
```
```json
{ "type": "complete", "message": "You've mastered this material." }
```

## Socratic tutor

Conversations are per user and optionally per topic. The tutor is guiding (Socratic):
it hints and asks questions rather than dumping answers, and every reply is grounded
in the topic's source chunks. Conversation history persists for continuity.

| Method | Path | Description |
|---|---|---|
| GET | `/api/tutor/conversations` | List the caller's conversations (newest activity first). |
| POST | `/api/tutor/conversations` | Start a conversation. Body: `{ "topic_id": 4, "title": null, "language": "en" }` (all optional; defaults to the topic title + the user's language). |
| GET | `/api/tutor/conversations/{id}` | Conversation with full message history. |
| POST | `/api/tutor/conversations/{id}/messages` | Send a message and get the tutor's reply. Body: `{ "content": "Why does this happen?" }`. |
| DELETE | `/api/tutor/conversations/{id}` | Delete a conversation and its messages. |

Reply response:

```json
{
  "user_message": { "id": 1, "role": "user", "content": "Why does this happen?",
    "grounding": [], "created_at": "2026-09-24T10:00:00Z" },
  "reply": { "id": 2, "role": "assistant",
    "content": "Great question — what do you think happens first?",
    "grounding": [ { "chunk_id": 3, "index": 1, "relevance": 0.82 } ],
    "created_at": "2026-09-24T10:00:01Z" }
}
```

> The student's message is persisted before the model call, so the conversation
> survives a provider outage. An LLM failure returns `502` and the message remains.

## Study planner

Exam dates and generated study plans. Plan generation is deterministic: the
student's topics are distributed across the days before the exam, weakest topics
first, respecting a daily study budget. No LLM is involved.

| Method | Path | Description |
|---|---|---|
| POST | `/api/planner/exams` | Create an exam date. Body: `{ "title": "Midterm", "exam_date": "2026-12-01", "subject_id": null }`. |
| GET | `/api/planner/exams` | List exam dates (soonest first). |
| DELETE | `/api/planner/exams/{id}` | Delete an exam and its plans. |
| POST | `/api/planner/plans` | Generate a plan. Body: `{ "exam_date_id": 1, "daily_minutes": 60, "subject_id": null }`. Archives any prior active plan. |
| GET | `/api/planner/plans` | List plans with progress. |
| GET | `/api/planner/plans/{id}` | Plan detail with scheduled items. |
| PATCH | `/api/planner/plans/{id}/items/{item_id}` | Mark an item. Body: `{ "status": "done" }` (or `"pending"`). |
| DELETE | `/api/planner/plans/{id}` | Delete a plan. |

Plan detail response:

```json
{
  "id": 1, "exam_date_id": 1, "status": "active", "created_at": "...",
  "exam_title": "Midterm", "exam_date": "2026-12-01",
  "total_items": 8, "completed_items": 2, "percent_complete": 0.25,
  "items": [
    { "id": 10, "topic_id": 4, "topic_title": "Photosynthesis",
      "scheduled_for": "2026-09-24", "estimated_minutes": 30,
      "status": "done", "completed_at": "..." }
  ]
}
```

## Gamification

Streaks advance on any activity (quiz, review, tutor message, plan item). Achievements
unlock automatically when their criteria are met; an unlock also raises a notification.

| Method | Path | Description |
|---|---|---|
| GET | `/api/gamification/streak` | Current/longest streak and today's activity count. |
| GET | `/api/gamification/achievements` | Achievement catalog with `unlocked` / `unlocked_at`. |
| GET | `/api/gamification/dashboard` | Aggregated progress: streak, topic coverage, average mastery, due reviews, achievements, active plan. |

## Notifications

In-app reminders for due reviews and today's plan tasks. Reminders are generated
idempotently (at most one of each type per user per day) when notifications are listed.

| Method | Path | Description |
|---|---|---|
| GET | `/api/notifications` | List notifications (query: `generate`, `unread_only`, `limit`). Returns `{ items, unread }`. |
| POST | `/api/notifications/{id}/read` | Mark one notification read. |
| POST | `/api/notifications/read-all` | Mark all read. Returns `{ "updated": n }`. |

## Admin & AI operations

Admin-only (`require_admin`; non-admin sees 403). AI usage is recorded
automatically for every generation call (structuring, teaching, quiz generation,
short-answer grading, tutor replies, adaptive messages) **and every embedding call**
(ingestion, retrieval) with provider, model, latency, token counts where the
provider reports them, and error status.

| Method | Path | Description |
|---|---|---|
| GET | `/api/admin/users` | List/search users (query: `q`, `page`, `page_size`). Returns `{ items, total, page, page_size }`. |
| GET | `/api/admin/users/{id}` | Fetch one user. |
| PATCH | `/api/admin/users/{id}` | Update display name / role / grade / active. |
| POST | `/api/admin/users/{id}/deactivate` | Deactivate and revoke sessions (self-deactivation blocked). |
| POST | `/api/admin/users/{id}/reactivate` | Reactivate a user. |
| GET | `/api/admin/ai-usage` | Recent AI usage rows (query: `limit`). |
| GET | `/api/admin/audit-logs` | Recent audit rows (query: `limit`). |

## Status codes

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 400 | Bad input (e.g. no file, unsupported type, quiz before lessons ready) |
| 404 | Not found |
| 409 | Conflict (e.g. material already processing) |
| 502 | Upstream AI provider error |
