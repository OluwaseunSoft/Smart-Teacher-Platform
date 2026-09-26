# Suhail Smart Teacher Platform — Product Overview

## 1. Vision

Suhail Smart Teacher is a web-based, AI-powered learning platform that behaves like a
personal teacher. A student drops in their own study material, and the system:

1. **Reads** it (PDF, plain text, notes).
2. **Organizes** it into a structured curriculum of concepts and lessons.
3. **Teaches** it in an adaptive, conversational way.
4. **Tests** understanding with generated assessments.
5. **Adapts** to how that specific student learns, based on their performance.

The differentiator is the *closed adaptive loop*: every quiz result feeds back into
what the teacher teaches next and how it teaches it.

## 2. Problem

- Students have raw material (textbooks, lecture notes, PDFs) but no structure.
- Generic chatbots answer questions but do not build or remember a curriculum.
- Existing study apps are either static (flashcards, PDFs) or generic (no adaptation).

## 3. Target users (MVP)

- **Primary:** Self-directed learners studying from their own material.
- **Later:** Teachers assigning material; institutions.

The MVP is **single-user** — no accounts, no tenancy. A local `Student` record is
auto-created so the data model is future-proof.

## 4. Core user journey (MVP)

1. Student uploads a PDF or pastes text.
2. Student clicks **Process**. The system ingests and extracts concepts.
3. The system generates a **lesson** for each concept.
4. Student opens a lesson, reads/hears the AI explanation.
5. Student takes the generated **quiz** for the lesson.
6. The system scores the quiz, updates per-concept **mastery**, and decides the
   **next step**: reteach, practice, or advance.
7. Repeat until the material is mastered.

## 5. The five capabilities

| Capability | What it does | Service |
|---|---|---|
| Read | Extract + chunk text from uploads | `services/ingestion.py` |
| Organize | Build concept graph + lesson plan | `services/structuring.py` |
| Teach | Generate adaptive lesson content | `services/teaching.py` |
| Test | Generate + grade assessments | `services/assessment.py` |
| Adapt | Track mastery, pick next step | `services/adaptive.py` |

## 6. Non-goals (MVP)

- No multi-user auth, roles, or sharing.
- No real-time collaboration.
- No mobile native app (responsive web only).
- No handwriting/OCR of images (PDF text layer only).
- No payment/billing.

## 7. Success criteria for the MVP

- A user can go from upload → processed material → lesson → quiz → adaptive
  recommendation without leaving the app.
- Processing survives a provider outage gracefully (clear error states).
- Switching AI provider (OpenAI / Anthropic / Ollama) requires only a config change.
- The whole thing runs locally with two commands (backend + frontend).

## 8. Key product decisions

- **Provider-agnostic AI.** All model calls go through one interface so we never
  lock into a vendor and can run fully offline via Ollama.
- **SQLite for MVP.** Zero-ops. Schema is Postgres-compatible for later migration.
- **Embeddings enable grounding.** Lessons and quizzes are grounded in retrieved
  source chunks, reducing hallucination.
- **Adaptation is explicit, not vibes.** Mastery is a computed number per concept;
  the next-step policy is deterministic and testable, with the LLM only phrasing the
  output.
