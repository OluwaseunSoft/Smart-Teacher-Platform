# Planning guide for larger tasks

Use this file as a lightweight planning template for big changes, cross-app work,
feature additions, migrations, or broader refactors.

## 1. Goal and scope

- Describe the business or technical goal in one paragraph.
- State what is in scope and what is explicitly out of scope.
- List any affected areas: backend, frontend, docs, database, infra, tests.

## 2. Working assumptions

- Capture the current state of the repo and any constraints.
- Note dependencies, external services, APIs, or hardware assumptions.
- Record the known risks, unknowns, and open questions.

## 3. Work breakdown

Break the task into phases and smaller units of work.

### Phase 1: Research and discovery

- Inspect the relevant code paths and tests.
- Identify existing patterns, contracts, and config surfaces.
- Confirm whether the change spans only one app or both frontend and backend.

### Phase 2: Design and decision points

- Document the chosen implementation strategy.
- Note important API contract changes, data model changes, and UI flows.
- Call out backwards-compatibility concerns or migration needs.

### Phase 3: Execution

- Create a task list with checkpoints.
- Keep each item small and reviewable.
- Prefer incremental validation over waiting for a final broad pass.

### Phase 4: Verification

- List the exact validation steps to run.
- Include backend pytest commands, TypeScript checks, and app-specific smoke tests.
- Confirm that the fix preserves existing behavior where relevant.

## 4. Task checklist

- [ ] Confirm repository instructions in `AGENTS.md`
- [ ] Identify affected frontend/backend files
- [ ] Define the API or data contract changes
- [ ] Add/update tests for behavior changes
- [ ] Implement changes in small, reviewable steps
- [ ] Validate with the smallest appropriate command
- [ ] Update docs or config if required
- [ ] Review final diff for scope and correctness

## 5. Example structure for a large task

### Task: Add a new API flow

- Backend:
  - route changes in `backend/app/api/...`
  - service logic in `backend/app/services/...`
  - schema updates in `backend/app/schemas.py`
- Frontend:
  - API client changes in `frontend/src/api/...`
  - screen updates in `frontend/src/pages/...`
  - shared UI updates in `frontend/src/components/...`
- Tests:
  - backend test coverage in `backend/tests/...`
  - frontend type-check/build validation in `frontend/`
- Docs:
  - update README or architecture docs if behavior changes

## 6. Outcomes and exit criteria

- Define what success looks like.
- Record the expected user-visible behavior or API behavior.
- Capture the acceptance checks that prove the work is complete.

## 7. Notes

- Keep this file practical and concise.
- Update it as the task evolves.
- If a task grows too large, break it into nested planning items rather than storing everything in one unstructured block.

## 8. Source of truth

For this repository, always check `AGENTS.md` before changing code, and keep work aligned with the existing frontend/backend separation and project structure.
