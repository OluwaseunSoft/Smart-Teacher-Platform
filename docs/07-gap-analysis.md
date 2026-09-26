# Gap Analysis — v2 Requirements vs. Current Scaffold

> Compares `06-v2-requirements.md` against the current Phase 0 scaffold (commit
> `76a37e9`, branch `develpment`). Used to sequence implementation.

## Summary

The scaffold implements a **single-user, English-only, no-auth MVP loop**. The v2
spec adds accounts, roles, authorization, bilingual/RTL, PWA, spaced repetition,
tutor, planner, gamification, notifications, and admin/AI-ops. Roughly **~30% of the
v2 data model** and **~0% of the v2 security/identity surface** exist today.

## Capability gaps

| Area | Tier | Current state | Gap |
|---|---|---|---|
| Accounts & auth | Core | None. Single auto-created `Student`. | User model, bcrypt hashing, JWT, sessions, refresh/logout, reset hooks, UI. |
| Roles & authz | Core | None. | Role field, `get_current_user`, `require_admin`, ownership checks on every scoped endpoint. |
| Ingestion | Core | `Material` + `Chunk` exist; PDF/text supported. | Rename/align to SourceDocument/SourceChunk; retry UX; upload limits. |
| Structuring | Core | Flat `Concept` with `parent_id` and `order_index`. | Explicit **Subject → Chapter → Topic** hierarchy; topic↔chunk grounding links. |
| Teaching | Core | `Lesson` per concept, `simpler` flag. | Language-aware generation; grounding refs; TTS/listen. |
| Assessment | Core | `Question`/`Attempt`/`Mastery` exist; MCQ grading. | Short-answer grading; deterministic next-step policy tests. |
| Socratic tutor | Core | None. | `TutorConversation`/`TutorMessage`, guiding prompt, persistence, grounding. |
| Spaced repetition | Core | None. | `ReviewSchedule` (SM-2-like), due queue, interval updates. |
| Study planner | Core | None. | `ExamDate`, `StudyPlan`, `StudyPlanItem`, generation + progress. |
| Gamification | Core | None. | Streaks, achievements, progress dashboard. |
| Notifications | Core | None. | `Notification` model + in-app center + reminder generation. |
| Bilingual AR/EN + RTL | Core | English only. | i18n framework, RTL, localized strings, per-user language. |
| Mobile-first / PWA | Core | Responsive web only. | Manifest, service worker, offline shell, mobile-first pass. |
| Accessibility | Core | Basic semantic HTML. | WCAG pass, keyboard nav, ARIA, focus management, contrast, reduced motion. |
| Admin & AI-ops | Core | None. | Admin console, user management, `AuditLog`, `AIUsageLog`. |
| Year rollover / tenancy | Advanced | None. | `AcademicYear`, `Institution`, scoping columns. |
| Teacher / Parent roles | Stretch | None. | Reserved role enum values; no endpoints yet. |

## Data model gaps

**Exists:** `Student`, `Material`, `Chunk`, `Concept`, `Lesson`, `Question`,
`Attempt`, `Mastery`, `StudySession`.

**Missing (Core):** `User`, `Session`, `StudentProfile`, `Subject`, `Chapter`,
`Topic`, `ReviewSchedule`, `TutorConversation`, `TutorMessage`, `ExamDate`,
`StudyPlan`, `StudyPlanItem`, `Achievement`, `UserAchievement`, `Streak`,
`Notification`, `AuditLog`, `AIUsageLog`.

**Missing (Advanced):** `AcademicYear`, `Institution` + tenancy scoping columns.

## API gaps

- No `/api/auth/*` (signup, login, refresh, logout, me, reset).
- No `/api/admin/*` (users, AI usage, audit).
- No tutor, review, planner, gamification, notification endpoints.
- Existing endpoints authenticate via `get_current_student()` which auto-creates a
  single student — must be replaced with real bearer-token auth + ownership checks.

## Frontend gaps

- No landing, auth, onboarding, dashboard, tutor, review, planner, progress,
  notifications, admin, or settings screens.
- API client has no auth token handling or 401 refresh.
- No i18n/RTL, no PWA configuration.

## Environment / dependency gaps

- `bcrypt 5.0.0` and `PyJWT 2.14.0` installed in the venv but **not in
  `requirements.txt`**.
- No migrations tool; relying on `Base.metadata.create_all`. Consider Alembic once
  schema churn increases.

## Recommended build order

1. **Foundation (this increment):** config + security utils + auth/role/session
   models + auth API + authz deps + admin user management + tests.
2. Curriculum hierarchy refactor (Subject/Chapter/Topic) with topic↔chunk links.
3. Spaced repetition + mastery v2.
4. Tutor.
5. Planner + gamification + notifications.
6. Frontend: auth/onboarding/dashboard, then i18n/RTL, then PWA/accessibility pass.
7. Admin/AI-ops UI + audit/AI usage logging.
8. Advanced: year rollover/tenancy.
