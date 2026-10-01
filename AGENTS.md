# Repository guidance

This repository contains two independently runnable applications:

- `frontend/`: React, TypeScript, Vite, and Tailwind CSS single-page app.
- `backend/`: FastAPI and SQLAlchemy API, services, and LLM providers.

Keep changes scoped to the relevant app, and preserve the HTTP contract between
the frontend and backend. Consult `docs/01-architecture.md` and
`docs/03-api-spec.md` when changing architecture or API behavior.

## General

- Follow the existing patterns and naming in the surrounding code.
- Keep credentials and local configuration in `.env`; never commit secrets.
  Update `.env.example` when adding or changing required configuration.
- Avoid committing generated output, virtual environments, dependency folders,
  local databases, or build artifacts.
- Update relevant design or API documentation when changing documented behavior.

## Frontend

- Work in `frontend/src/`; keep API calls and shared request behavior in
  `src/api/`, reusable UI in `src/components/`, and routed screens in
  `src/pages/`.
- Keep request and response types aligned with the backend schemas. Use the
  existing API client rather than issuing ad hoc requests from screens.
- The Vite development server proxies `/api` to `http://localhost:8000`.
- From `frontend/`, run `npm run typecheck` for TypeScript validation and
  `npm run build` for the production build. There are no configured frontend
  lint or test scripts.

## Backend

- Keep HTTP handling in `app/api/`, business logic in `app/services/`, data
  models in `app/models.py`, request/response schemas in `app/schemas.py`, and
  provider-specific code behind the interface in `app/llm/`.
- Keep route handlers thin and put reusable or domain-specific behavior in the
  service layer. Preserve the provider-agnostic LLM interface when adding or
  changing providers.
- Add or update tests in `tests/` for behavior changes. Tests use pytest and
  in-memory SQLite fixtures; avoid requiring live databases or LLM services.
- From `backend/`, run `python -m pytest`. The project configures pytest to
  discover tests under `tests/`.
- Keep runtime configuration in `app/config.py` and document new environment
  variables in the root `README.md` and `backend/.env.example`.
