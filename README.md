# Suhail Smart Teacher Platform

A web-based, AI-powered learning platform that works like a personal teacher: it
**reads** your study material, **organizes** it into concepts, **teaches** it,
**tests** you, and **adapts** to how you learn.

![loop](https://img.shields.io/badge/loop-read%20→%20organize%20→%20teach%20→%20test%20→%20adapt-indigo)

---

## What's here

This repository contains the design documentation and a runnable scaffold for the
single-user MVP core loop.

```
suhail-smart/
├─ docs/                 Design documentation (start here)
│  ├─ 00-overview.md     Product overview / PRD
│  ├─ 01-architecture.md System architecture
│  ├─ 02-data-model.md   Entities, relationships, mastery rule
│  ├─ 03-api-spec.md     HTTP API contract
│  ├─ 04-ai-pipeline.md  The five AI stages
│  └─ 05-roadmap.md      Phased plan, risks, definition of done
├─ backend/              FastAPI + SQLAlchemy (Python)
└─ frontend/             React + Vite + TypeScript + Tailwind
```

## Core loop

1. **Read** — upload a PDF or paste text (`services/ingestion.py`).
2. **Organize** — LLM builds an ordered concept graph (`services/structuring.py`).
3. **Teach** — grounded lessons generated per concept (`services/teaching.py`).
4. **Test** — quizzes generated + graded (`services/assessment.py`).
5. **Adapt** — mastery tracked, next step chosen (`services/adaptive.py`).

## Provider-agnostic AI

All model calls go through one interface (`backend/app/llm/`). Switch providers with
environment variables — no code changes. OpenAI, Anthropic, and a fully local
**Ollama** option are included.

| Capability | Default | Options |
|---|---|---|
| Generation | `ollama` | `openai`, `anthropic`, `ollama` |
| Embeddings | `ollama` | `openai`, `ollama` |

---

## Quickstart

### 1. Backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env      # then edit if needed
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

By default it expects a local Ollama server. Fully local setup:

```powershell
ollama pull llama3.1
ollama pull nomic-embed-text
```

Or use a hosted provider — edit `backend/.env`:

```env
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

```env
LLM_PROVIDER=anthropic
EMBEDDING_PROVIDER=ollama     # Anthropic has no embeddings API
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Frontend (React SPA)

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to the backend on port 8000.

### 3. Use it

1. Add a PDF or paste text → **Add material**.
2. Open it → **Process material** (runs the full pipeline).
3. Open a lesson, **Take the quiz**.
4. **Start study session** and let the adaptive engine guide you.

### Run with Docker

Docker Compose starts the frontend, API, and Ollama. The frontend is served on
http://localhost:8080 and forwards `/api` requests to the backend. The backend
API and Swagger UI are also available at http://localhost:8000 and
http://localhost:8000/docs.

```powershell
Copy-Item backend\.env.example backend\.env
docker compose up --build -d
docker compose exec ollama ollama pull llama3.1
docker compose exec ollama ollama pull nomic-embed-text
```

Ollama downloads model weights into a named volume on the first pull; the
downloads are not part of either application image. The backend installs the
Python requirements, including the OpenAI and Anthropic SDKs. To use either
hosted provider instead of Ollama, set `LLM_PROVIDER`, `EMBEDDING_PROVIDER`,
and the relevant API key in `backend/.env`. Keep `OLLAMA_BASE_URL` as provided
when using Ollama in Compose; the Compose network routes it to the Ollama
container.

SQLite data and Ollama model files persist in named volumes. Stop the services
without deleting data with `docker compose down`; `docker compose down -v`
removes those volumes and their contents. Replace the development
`AUTH_SECRET_KEY` before exposing a deployment to users.

---

## Development

```powershell
# backend tests (no LLM required)
cd backend
.\.venv\Scripts\python.exe -m pytest

# frontend typecheck + production build
cd frontend
npm run build
```

## Configuration reference

| Variable | Purpose | Default |
|---|---|---|
| `LLM_PROVIDER` | generation backend | `ollama` |
| `EMBEDDING_PROVIDER` | embedding backend | `ollama` |
| `LLM_MODEL` / `EMBEDDING_MODEL` | model names | provider defaults |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | credentials | empty |
| `OLLAMA_BASE_URL` | local inference | `http://localhost:11434` |
| `DATABASE_URL` | database | `sqlite:///./suhail.db` |
| `CORS_ORIGINS` | allowed origins | `http://localhost:5173` |
| `RETRIEVAL_TOP_K` | grounding chunks per query | `5` |

## Status

Phase 0 (design + scaffold) is complete. The backend runs, the SPA builds, and the
full core loop is wired. See [`docs/05-roadmap.md`](docs/05-roadmap.md) for what's
next — starting with end-to-end validation against a live provider.
