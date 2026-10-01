# Code review guide

Use this guide when reviewing changes in this repository. Focus on correctness,
regressions, security, and maintainability; report actionable findings rather
than stylistic preferences.

## Review priorities

Review changes in this order:

1. **Correctness:** Does the change meet its intended behavior? Are edge cases
   and failure paths handled?
2. **Regression risk:** Could existing frontend flows, API consumers, stored
   data, or provider configurations behave differently?
3. **Security and privacy:** Are authorization, input handling, secrets, and
   user data protected?
4. **Reliability:** Are external-service errors and unavailable resources
   surfaced clearly? Are state transitions and database transactions sound?
5. **Maintainability:** Does the implementation follow existing app boundaries
   and avoid unnecessary duplication or complexity?
6. **Verification:** Are meaningful tests present, and are the appropriate
   checks run?

## Repository-specific checks

### Backend (`backend/`)

- API handlers belong in `app/api/`; reusable domain logic belongs in
  `app/services/`. Check that routes do not take on service responsibilities.
- Keep request and response behavior aligned across routes and schemas in
  `app/schemas.py`; consider whether existing clients remain compatible.
- Review SQLAlchemy changes in `app/models.py` and `app/db.py` for relationship,
  transaction, persistence, and SQLite behavior.
- Check authentication and authorization paths, input validation, and error
  responses. Do not expose credentials, internal traces, or unintended user
  data.
- Keep model-provider-specific behavior in `app/llm/` behind the shared
  interface. Verify provider errors and configuration are handled explicitly.
- Prefer tests using the existing in-memory database fixtures. Tests should not
  require live LLM providers or external services unless explicitly intended.

### Frontend (`frontend/`)

- Keep screens, shared components, and API calls in their existing areas:
  `src/pages/`, `src/components/`, and `src/api/`.
- Check loading, empty, success, and error states for user-facing flows.
- Ensure API request/response types and authentication behavior match the
  backend contract. Avoid duplicating request behavior outside the shared API
  client without a clear reason.
- Review navigation and UI changes for accessibility, responsive layout, and
  consistency with existing patterns.
- Avoid logging tokens or sensitive user data in the browser.

### Changes spanning both apps

- Trace the complete request/response flow from the UI through the API to
  persistence or provider calls, then back to the UI.
- Check that status values, identifiers, validation rules, and error shapes
  agree on both sides.
- Consider older or partially completed records and existing clients when
  changing API or stored-data behavior.
- Update the relevant API or architecture documentation when contracts or
  system behavior change.

## Tests and checks

Run the smallest checks that meaningfully cover the change:

- Backend: from `backend/`, run `python -m pytest` or the relevant test module.
- Frontend: from `frontend/`, run `npm run typecheck`; use `npm run build` for
  production-build validation.
- For cross-app changes, validate both sides and, where practical, exercise the
  full user flow.

Do not treat a passing build or test suite as proof that behavior is correct;
check that tests cover the changed behavior and important failure cases.

## Writing findings

- Report issues before general summaries, ordered by severity.
- State the affected file and line, the specific failure scenario, and the
  user, data, or system impact.
- Suggest a focused remediation when it helps clarify the issue.
- Distinguish verified defects from questions or suggestions. Avoid reporting
  purely stylistic preferences as defects.
- If no actionable issues are found, say so and note any important validation
  that was not run.

## Review completion checklist

- [ ] The change matches the stated behavior and scope.
- [ ] Relevant edge cases and failure paths are accounted for.
- [ ] API, frontend, database, and provider contracts remain consistent.
- [ ] Sensitive data and authorization boundaries are protected.
- [ ] Tests cover the changed behavior and appropriate checks pass.
- [ ] Related documentation and configuration examples are up to date.
