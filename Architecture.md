# Architecture change guide

Use this guide when a change affects system boundaries, core data flows,
deployment or runtime structure, persistence, API contracts, or shared
cross-cutting behavior. For routine implementation work within an existing
boundary, follow the current design documented in `docs/01-architecture.md`.

## Current system boundaries

- `frontend/` is a React, TypeScript, and Vite single-page app.
- `backend/` is a FastAPI application with SQLAlchemy persistence.
- The frontend communicates with the backend over HTTP/JSON using `/api/*`.
- API handlers live in `backend/app/api/`; domain operations live in
  `backend/app/services/`.
- Database models are in `backend/app/models.py`; request and response schemas
  are in `backend/app/schemas.py`.
- AI integrations live in `backend/app/llm/` behind a provider-agnostic
  interface. Generation and embedding providers may be configured separately.
- The current MVP uses SQLite and in-process retrieval. Do not assume that a
  production migration path, worker, or external vector database already
  exists.

## When to write an architecture proposal

Document the change before implementation when it:

- Adds, removes, or changes a runtime, service, or major module boundary.
- Changes an API contract used by the frontend or another consumer.
- Changes persistent data structures, database technology, or migration
  behavior.
- Changes how material processing, tutoring, assessment, or adaptive study
  flows are orchestrated.
- Adds a background worker, queue, cache, vector store, or external service.
- Changes authentication, authorization, tenancy, or handling of sensitive
  data across components.
- Introduces a cross-cutting design decision with meaningful operational,
  compatibility, or maintenance consequences.

## Architecture proposal template

Copy and complete the sections below for a substantial architecture change.
Keep decisions concise and record alternatives only when they are genuinely
viable.

### Title and status

- **Title:**
- **Status:** Proposed / Accepted / Rejected / Superseded
- **Date:**
- **Owners:**

### Context and problem

Describe the current behavior, the problem to solve, why it matters, and the
constraints that influence the design.

### Goals and non-goals

- **Goals:** What outcomes must the design provide?
- **Non-goals:** What related work is intentionally excluded?

### Proposed design

Describe the components involved, their responsibilities, and how data and
control flow between them. Include a diagram when it makes the flow clearer.
Identify affected areas in the frontend, backend, API, persistence, and
external integrations.

### Contracts and data

- Document API request/response changes and error behavior.
- Document model or schema changes, data ownership, and migration or
  backfill requirements.
- Explain compatibility with existing clients and stored records.
- Specify relevant validation and authorization boundaries.

### Alternatives considered

List realistic alternatives and briefly state why the proposed design is
preferred.

### Risks and mitigations

Cover failure modes, data loss or corruption, latency, provider availability,
security and privacy, operational complexity, and rollback needs.

### Rollout and rollback

Describe required configuration, deployment order, migrations, feature gates,
monitoring, and how to safely disable or reverse the change.

### Verification and acceptance criteria

List observable outcomes and concrete checks. Include relevant backend tests,
frontend typecheck/build, API or integration checks, migration validation, and
manual smoke tests as appropriate.

### Documentation updates

Identify the repository documentation and configuration examples that must
change, including `docs/01-architecture.md`, `docs/03-api-spec.md`,
`README.md`, and `.env.example` when applicable.

## Implementation and review

- Preserve existing boundaries unless the proposal intentionally changes them.
- Keep API handlers thin and reusable domain behavior in services.
- Keep provider-specific behavior behind the LLM interface.
- Make compatibility and migration behavior explicit; do not silently discard
  or reinterpret persisted data.
- Surface dependency failures and invalid states clearly rather than hiding
  them behind success-shaped defaults.
- Add tests for the new behavior and important failure cases at the layer where
  the behavior belongs.
- Update the architecture and API documentation alongside implementation.
- Review the proposal and implementation together to ensure the delivered
  design matches the accepted decision.

## Architecture change checklist

- [ ] The problem, goals, and non-goals are clear.
- [ ] Component responsibilities and data flows are documented.
- [ ] API and persistence contracts are accounted for.
- [ ] Compatibility, migration, rollout, and rollback are addressed.
- [ ] Security, privacy, reliability, and operational risks are considered.
- [ ] Alternatives and significant trade-offs are recorded.
- [ ] Tests and acceptance criteria verify the actual behavior.
- [ ] Relevant architecture, API, and setup documentation is updated.
