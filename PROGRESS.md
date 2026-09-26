# Progress & Handoff

_Last updated: 2026-09-25_

This file is the continuity log for the Suhail Smart Teacher build. Read this first
when resuming work.

## Where we are

- **Branch:** `develpment`
- **Last commit:** `76a37e9` — "Add progress and handoff log"
- **Push status:** ⚠️ **NOT pushed.** `git push -u origin develpment` is blocked on
  Bitbucket authentication (Git Credential Manager needs an app password). See
  "Resume checklist" below.
- **Overall status:** Phase 0 (design + scaffold) complete and verified. **v2 Core
  increments 1 (auth foundation), 2 (curriculum hierarchy + endpoint auth migration
  + frontend auth gate), 3 (spaced repetition + mastery v2), 4 (Socratic tutor),
  5 (planner + gamification + notifications), 6 (frontend app shell, feature
  screens, i18n + RTL, PWA), 7 (admin/AI-ops console) and 8 (AI usage logging)
  implemented and verified (uncommitted).** Demo seed data (`app.seed`) also added.
  **v2 Core increment 9 (hardening: adaptive/assessment tests + list-state error
  handling) also implemented and verified (uncommitted).**   **Increment 10 (demo
  mastery history + embedding AI-usage logging) implemented and verified
  (uncommitted).** **Increment 11 (accessibility + UX hardening) implemented and
  verified (uncommitted; frontend-only).**

## v2 Core increment 11 — Accessibility & UX hardening (uncommitted)

WCAG-aware pass over the student + admin UI (frontend-only).

### Frontend
- `index.css` — global `:focus-visible` outline; `prefers-reduced-motion` media
  query that neutralises animations/transitions; logical `padding-inline-start` /
  `border-inline-start` in lesson prose so RTL lists/quotes render correctly.
- `components/ui.tsx` — `Spinner` is now `role="status"` + `aria-live="polite"`
  (with a fallback label); `ErrorText` is `role="alert"` so failures are announced.
- `components/Layout.tsx` — route change focuses `<main tabIndex={-1}>` and scrolls
  to top; notification bell `aria-label` includes the unread count and the visual
  badge is `aria-hidden`.
- `components/QuizRunner.tsx` — MCQ options wrapped in a labelled `radiogroup`
  bound to the question; short-answer textarea labelled; result container receives
  focus and the score is announced via `role="status"`; RTL `text-end`.
- Forms — every `<label>` is now associated via `htmlFor`/`id` and password/email/
  name inputs declare `autoComplete` (Login, Onboarding, Settings, Planner, Tutor,
  Admin search, Materials, Quiz).
- `MaterialsPage` — source toggle is a `tablist` with `aria-selected`; file/title/
  textarea inputs labelled; list query error + gated empty state.
- `AdminPage` — all `<th scope="col">`; tabs expose `aria-controls` + `tabpanel`
  roles; failed AI-usage rows include an sr-only error message.
- `NotificationsPage` — added `notifications.markRead` (EN/AR) replacing the
  mislabelled "Close"; mark-read button has a per-item `aria-label`; empty state is
  gated on load/error.
- `ProgressPage`/`DashboardPage` — mastery/plan bars are `role="progressbar"` with
  `aria-valuenow`; mastery empty state gated on load/error.
- `ReviewsPage` — quality buttons grouped with an `aria-label`; `TutorPage`
  conversation log is `role="log" aria-live="polite"` with a labelled compose box.
- RTL correctness — swapped physical directional utilities for logical ones
  (`pl-pr`/`ml-mr`/`left`/`border-l` → `ps-pe`/`ms-me`/`start`/`border-s`) in the
  skip link, lesson lists, curriculum indent, quiz status stripe, and file input.

## v2 Core increment 10 — Demo mastery history + embedding usage logs (uncommitted)

Populated the demo mastery timeline and extended AI-usage logging to embedding calls.

### Backend
- `app/seed.py` — `_seed_progress` now writes one `MasteryEvent` per simulated
  attempt (score/delta/`is_correct`/`source="quiz"` + historical `created_at`), so
  the demo student has a populated mastery timeline; seed result now reports
  `mastery_events`.
- `app/llm/base.py` — `LLMProvider.last_model` (+ providers set it in
  `complete`/`embed`) so the usage log records the model actually used
  (embedding model for embeddings).
- `app/services/ai_usage.py` — `track_ai` prefers `provider.last_model`, falling
  back to `provider.model` (keeps existing fake providers working).
- `app/services/ingestion.py` — `ingest(text, *, db=None, user_id=None)` logs the
  embedding call as `ingestion.embed` (committed immediately) and still degrades
  gracefully to lexical retrieval on failure.
- `app/services/retrieval.py` — `rank_chunks`/`retrieve` accept `user_id` and log
  `retrieval.embed` when a query embedding is computed (persisted on the caller's
  next commit).
- Wired `user_id` through `pipeline.process_material`, `structuring._ground_topic`,
  `teaching.generate_lesson`, `assessment.generate_quiz`, and `tutor.topic_context`.
- `tests/test_ai_usage.py` — +3 tests (ingestion embed logged, ingestion embed
  failure logged as `status="error"` + degrades, retrieval embed logged).
- `tests/test_seed.py` — NEW (3 tests): mastery events == attempts and linked to
  topics, events ordered/mixed correctness, seed idempotency.

## v2 Core increment 9 — Hardening + missing tests (uncommitted)

Closed the outstanding test gaps for the adaptive policy and assessment grading, and
removed a real MCQ-grading bug; hardened list-screen error/empty states.

### Backend
- `app/services/assessment.py` — **BUG FIX**: option-letter answers with a suffix
  (e.g. `"b)"`) never matched because the f-string dropped the call:
  `f"{letter.lower})"` → `f"{letter.lower()})"`. Caught by the new tests.
- `tests/test_adaptive.py` — NEW (8 tests): `next_action` policy — complete with no
  concepts / missing material, advance from unstarted, advance skips mastered
  topics, reteach when weak (`< 0.4`), practice when midway (with quiz payload),
  complete + `session.status="completed"` once everything is mastered. LLM message
  calls are monkeypatched; lessons/questions are seeded so no provider is needed.
- `tests/test_assessment.py` — NEW (8 tests): MCQ grading (case/whitespace
  normalisation, option-letter `"B"`/`"b)"`, wrong answer, empty response),
  short-answer grading via a fake provider (success + provider-misbehaviour
  fallback), `_difficulty` clamping, `generate_quiz` idempotency (no provider call
  when questions exist) and type normalisation (`weird`→mcq, missing options→short,
  prompt-less items skipped).

### Frontend
- `MaterialsPage.tsx` — list query now renders an `ErrorText` on failure and only
  shows the empty state when neither loading nor errored.
- `PlannerPage.tsx` — same for exams, plans, and the curriculum subject select.
- `TutorPage.tsx` — same for the conversation list and curriculum topic select.
- `MaterialDetailPage.tsx` — surfaces concepts/lessons fetch errors instead of
  silently showing `0 concepts`.

Note: `material.status` polling was already present on both `MaterialsPage` and
`MaterialDetailPage` (`refetchInterval` while `processing`), so no change needed.

## v2 Core increment 8 — AI usage logging (uncommitted)

Every LLM generation call now writes an `AIUsageLog` row, so the admin AI usage
tab is populated. Token counts are captured where the provider reports them.

### Backend
- `app/llm/base.py` — `LLMProvider` gains `model` + `last_usage` (updated per call,
  never mutated in place).
- `app/llm/openai_provider.py`, `anthropic_provider.py`, `ollama_provider.py` — set
  `self.model`; capture `resp.usage` (OpenAI `prompt_tokens`/`completion_tokens`,
  Anthropic `input_tokens`/`output_tokens`, Ollama `prompt_eval_count`/`eval_count`).
- `app/services/ai_usage.py` — NEW: `track_ai(db, provider, operation, *, user_id,
  commit)` context manager. Adds the row to the **caller's** session (so tests stay
  isolated) and relies on the caller's commit; commits on error (caller is about to
  abort) and when `commit=True` (call sites with no later commit). Best-effort:
  never masks the provider result/exception.
- Wired call sites: `structuring.build_curriculum` (`structuring`),
  `teaching.generate_lesson` (`teaching.generate_lesson`),
  `assessment.generate_quiz` (`assessment.generate_quiz`),
  `assessment.grade_answer` (`assessment.grade`, now takes optional `db`/`user_id`,
  passed from `api/quizzes.py`), `tutor.ask` (`tutor.reply`), and
  `adaptive._message` (`adaptive.message`, `commit=True`).
- `app/services/__init__.py` — export `ai_usage`.
- `tests/test_ai_usage.py` — NEW (4 tests: structuring log, tutor log + user_id,
  short-answer grading log, provider failure logs `status="error"`).
- `docs/03-api-spec.md` — added "Admin & AI operations" section (also documents the
  previously-undocumented admin endpoints).

## v2 Core increment 7 — Admin / AI-ops console (uncommitted)

Admin-only UI over the existing `/api/admin/*` endpoints: user management, AI usage
monitoring, and audit log viewing. Global EN/AR + RTL via the shared i18n provider.

### Frontend
- `src/types.ts` — `AdminUserPage`, `AdminUserUpdate`, `AIUsageLog`, `AuditLog`.
- `src/api/client.ts` — `listAdminUsers` (search + pagination),
  `updateAdminUser`, `deactivateAdminUser`, `reactivateAdminUser`,
  `listAiUsage`, `listAuditLogs`.
- `src/pages/AdminPage.tsx` — NEW: role-guarded console with Users / AI usage /
  Audit tabs. Users tab: debounce-free search form, paginated table, activate /
  deactivate actions (self-deactivation hidden, mirrors server rule). AI usage tab:
  provider/model/operation/tokens/latency/status. Audit tab: actor/action/target/meta.
- `src/App.tsx` — `RequireAdmin` guard + `/admin` route (redirects non-admins to `/`).
- `src/components/Layout.tsx` — conditional Admin nav link for `role === "admin"`.
- `src/i18n.tsx` — `nav.admin` + `admin.*` keys in EN and AR.

## v2 Core increment 6 — Frontend app shell + feature screens (uncommitted)

Full student-facing UI over the increment 1–5 APIs: dashboard, onboarding, tutor,
reviews, planner, progress, notifications, settings; bilingual EN/AR with RTL; PWA
manifest + service worker; accessibility affordances.

### Frontend
- `src/types.ts` — extended with curriculum, review, mastery, tutor, planner,
  gamification, notification, and profile types.
- `src/api/client.ts` — new methods for curriculum, reviews, mastery, tutor,
  planner, gamification, notifications, and `PATCH /auth/me`.
- `src/i18n.tsx` — NEW: `I18nProvider`/`useI18n`, EN + AR dictionaries, dot-key
  `t()` with `{var}` interpolation, language persisted to `suhail.language`, sets
  `document.documentElement.lang`/`dir`; falls back to browser language.
- `src/components/Layout.tsx` — NEW: header nav (Dashboard, Library, Tutor,
  Reviews, Planner, Progress), notification bell with unread count, language
  selector, responsive wrap, skip link, `<Outlet/>`.
- `src/pages/` — NEW: `DashboardPage`, `OnboardingPage`, `TutorPage`,
  `ReviewsPage`, `PlannerPage`, `ProgressPage`, `NotificationsPage`,
  `SettingsPage`.
- `src/auth.tsx` — added `refresh()` to the auth context (used by onboarding /
  settings after profile updates).
- `src/lib/onboarding.ts` — NEW: per-user `suhail.onboarded:<id>` flag.
- `src/App.tsx` — route table (Layout parent route), onboarding redirect for
  students with no grade who have not completed onboarding, profile→i18n language
  sync.
- `src/main.tsx` — wraps app in `I18nProvider`; registers `/sw.js` in production.
- `public/manifest.webmanifest`, `public/icon.svg`, `public/sw.js` — NEW: PWA
  manifest, icon, and app-shell cache-first service worker (network-only for
  `/api/*`).
- `index.html` — manifest/theme-color/icon/description links.

## v2 Core increment 5 — Planner + gamification + notifications (uncommitted)

Deterministic study planner, daily streaks + achievements + dashboard, and
in-app reminder notifications.

### Backend
- `app/services/planner.py` — NEW: exam-date CRUD, `ordered_topics` (weakest first,
  then curriculum order), `generate_plan` (distributes topics across days before the
  exam under a `daily_minutes` budget; archives prior active plan),
  `plan_items`/`set_item_status`/`progress`, difficulty → estimated minutes.
- `app/services/gamification.py` — NEW: `DEFAULT_ACHIEVEMENTS` (7), `ensure_achievements`,
  `record_activity` (per-day `Streak` + `StudentProfile` streak current/longest/last),
  `compute_stats`, `evaluate` (criteria-based unlock), `record_and_evaluate`,
  `user_achievements`, `streak_summary`.
- `app/services/notifications.py` — NEW: `create`, `list_notifications`,
  `unread_count`, `mark_read`/`mark_all_read`, `generate_reminders` (idempotent
  per-day review-due + plan-task reminders), `notify_unlocked`.
- `app/schemas.py` — planner, gamification, and notification schemas.
- `app/api/planner.py` — NEW: `/api/planner/exams` (POST/GET/DELETE),
  `/api/planner/plans` (POST/GET), `/api/planner/plans/{id}` (GET/DELETE),
  `/api/planner/plans/{id}/items/{item_id}` (PATCH).
- `app/api/gamification.py` — NEW: `/api/gamification/streak`,
  `/achievements`, `/dashboard` (coverage, average mastery, due reviews, active plan).
- `app/api/notifications.py` — NEW: `GET /api/notifications`,
  `POST /notifications/{id}/read`, `POST /notifications/read-all`.
- Activity wiring: quiz submit (`gamification.record_and_evaluate` with `quiz_score`
  context), review submit, tutor conversation create/message, and plan item
  completion all advance streaks/evaluate achievements; unlocks raise notifications.
- `app/api/__init__.py` / `app/main.py` — register `planner`, `gamification`,
  `notifications` routers.
- `app/services/__init__.py` — export `planner`, `gamification`, `notifications`.
- `tests/test_planner.py` (6), `tests/test_gamification.py` (7),
  `tests/test_notifications.py` (5) — NEW.
- `docs/03-api-spec.md` — added "Study planner", "Gamification", "Notifications"
  sections.

## v2 Core increment 4 — Socratic tutor (uncommitted)

Guided (not answer-dumping) conversational tutor per topic, grounded in source
chunks, with persisted conversations/messages.

### Backend
- `app/prompts/tutor.py` — NEW: `TUTOR_SYSTEM` (Socratic rules: one question at a
  time, hints not answers, ground in sources, short replies, mirror language) and
  `tutor_system(...)` context builder (topic, summary, excerpts, mastery-aware
  scaffolding).
- `app/services/tutor.py` — NEW: `create_conversation`, `list_conversations`,
  `get_conversation`, `messages`, `message_count`, `topic_context` (grounding via
  `rank_chunks`), `ask` (persists the student message, calls the LLM with the last
  `MAX_HISTORY=20` turns, persists the grounded reply), `delete_conversation`.
- `app/models.py` — `TutorConversation.topic`/`.messages` and
  `TutorMessage.conversation` relationships (cascade delete-orphan).
- `app/schemas.py` — `TutorMessageOut`, `TutorConversationCreateIn`, `TutorAskIn`,
  `TutorConversationOut`, `TutorConversationSummaryOut`,
  `TutorConversationDetailOut`, `TutorReplyOut`.
- `app/api/tutor.py` — NEW: `GET/POST /api/tutor/conversations`, `GET/DELETE
  /api/tutor/conversations/{id}`, `POST /api/tutor/conversations/{id}/messages`
  (502 on provider failure; user message retained).
- `app/api/__init__.py` / `app/main.py` — register `tutor.router`.
- `app/prompts/__init__.py`, `app/services/__init__.py` — export `tutor`.
- `tests/test_tutor.py` — NEW (7 tests: auth, create/list, grounded reply +
  persistence, owner scoping, foreign-topic rejection, cascade delete, 502 keeps
  user message).
- `docs/03-api-spec.md` — added "Socratic tutor" section.

## v2 Core increment 3 — Spaced repetition + mastery v2 (uncommitted)

SM-2-like review scheduling, due queue, mastery history, and topic-level mastery.

### Backend
- `app/models.py` — NEW `MasteryEvent` (student_id, concept_id, topic_id, score,
  delta, is_correct, source, created_at): immutable mastery history.
- `app/services/repetition.py` — NEW: SM-2 core (`DEFAULT_EASE=2.5`, `MIN_EASE=1.3`,
  `MAX_EASE=2.8`, `PASS_QUALITY=3`, `MAX_INTERVAL_DAYS=365`); `get_or_create_schedule`,
  `apply_review`, `record_review`, `due_reviews`, `is_due`, `review_strength`,
  `quality_from_score`, `clamp_quality`. Naive-UTC normalisation for SQLite.
- `app/services/adaptive.py` — `update_mastery` now appends a `MasteryEvent` (with
  topic lookup) and takes optional `source`; added `topic_mastery`,
  `topic_mastery_map`, `mastery_history`.
- `app/services/__init__.py` — exports `repetition`.
- `app/api/deps.py` — added `owned_topic` (topic → chapter → subject → material,
  404 on mismatch).
- `app/api/reviews.py` — NEW: `GET /api/reviews` (`due_only`), `GET
  /api/reviews/queue` (`limit`), `GET /api/reviews/summary`, `POST
  /api/reviews/{topic_id}` (`{quality: 0-5}`).
- `app/api/mastery.py` — NEW: `GET /api/mastery` (per-topic), `GET
  /api/mastery/topics/{topic_id}/history`.
- `app/api/quizzes.py` — quiz submission now also updates the topic's review
  schedule (`quality_from_score`).
- `app/schemas.py` — `ReviewScheduleOut`, `ReviewQueueOut`, `ReviewSummaryOut`,
  `ReviewSubmitIn`, `TopicMasteryOut`, `MasteryEventOut`.
- `app/main.py` / `app/api/__init__.py` — register `reviews`, `mastery` routers.
- `tests/test_repetition.py` (5 tests) + `tests/test_reviews.py` (6 tests) NEW.

## v2 Core increment 2 — Curriculum hierarchy + auth migration (uncommitted)

Subject → Chapter → Topic hierarchy with topic↔chunk grounding; legacy resource
endpoints migrated to real auth + ownership; curriculum API; frontend auth gate.

### Backend
- `app/models.py` — `Student.user_id` FK→`users.id` (unique, nullable, indexed) +
  `user` relationship / `User.student` back_populates. `Subject.material_id` FK +
  `user_id` + `chapters`. `Chapter` `subject`/`topics`. `Topic` `chapter`/`concept`/
  `chunk_links`/`lessons`. `TopicChunk` unique `(topic_id, chunk_id)` + `topic`/`chunk`.
  `Lesson` gained `topic_id` FK, `language` (default `"en"`), `grounding` JSON.
  `Material.subjects` relationship.
- `app/services/structuring.py` — REWRITTEN: `build_curriculum` produces
  `Subject`→`Chapter`→`Topic`, one `Concept` per topic, `_ground_topic` via
  `rank_chunks`; returns `list[Concept]`.
- `app/services/retrieval.py` — added `rank_chunks(db, material_id, query, k) ->
  list[tuple[Chunk, float]]` (embeddings when present, else `_lexical_ranked`);
  `retrieve` delegates.
- `app/services/teaching.py` — `generate_lesson` uses `rank_chunks`, sets `topic_id`,
  `language`, `grounding=[{chunk_id,index}]`.
- `app/services/pipeline.py` — clears previous curriculum before rebuild.
- `app/api/deps.py` — removed legacy `get_current_student(db)`; added
  `current_student(user, db)` (auto-creates `Student`) and
  `owned_material(db, material_id, student)` (404 on mismatch).
- `app/api/materials.py`, `lessons.py`, `quizzes.py`, `sessions.py` — migrated to
  `current_student` + ownership checks.
- `app/schemas.py` — `LessonOut` +`topic_id`/`language`/`grounding`; curriculum
  schemas (`GroundingRef`, `TopicOut`, `TopicDetailOut`, `ChapterOut`, `SubjectOut`,
  `CurriculumOut`).
- `app/api/curriculum.py` — NEW: `GET /api/curriculum`,
  `GET /api/curriculum/materials/{id}`, `GET /api/topics/{id}`.
- `app/main.py` — registers `curriculum.router`.
- `tests/` — `test_curriculum.py` NEW (6 tests).

### Frontend
- `src/api/authToken.ts` — NEW: token storage (`suhail.access_token` /
  `suhail.refresh_token`).
- `src/api/client.ts` — attaches `Authorization: Bearer`; 401 clears tokens and
  dispatches `suhail:unauthorized`; adds `signup`/`login`/`logout`/`me`.
- `src/auth.tsx` — NEW: `AuthProvider` + `useAuth` (restores session via `/auth/me`,
  listens for unauthorized).
- `src/pages/LoginPage.tsx` — NEW: login/signup toggle.
- `src/App.tsx` — auth gate (spinner → `LoginPage` → app), header shows user + Sign out.
- `src/main.tsx` — wraps app in `AuthProvider`.
- `src/types.ts` — added `User`, `TokenResponse`.

## v2 requirements & gap analysis

- `docs/06-v2-requirements.md` — consolidated, authoritative v2 requirements
  (features A–O, roles, data model, NFRs, rating rubric, out-of-scope, tiering
  Core/Advanced/Stretch).
- `docs/07-gap-analysis.md` — current-capability vs v2 gaps and recommended build
  order. Supersedes the framing in `docs/00-overview.md` / `05-roadmap.md`.

## v2 Core increment 1 — Auth foundation (uncommitted)

Roles/authz, bcrypt + JWT sessions, audit logging, admin user & AI-ops APIs.

### Backend
- `app/security.py` — NEW: bcrypt hashing, JWT issue/verify (access/refresh/reset),
  `TokenError`.
- `app/models.py` — added `User`, `UserSession`, `StudentProfile`, `Institution`,
  `AcademicYear`, `Subject`, `Chapter`, `Topic`, `TopicChunk`, `ReviewSchedule`,
  `TutorConversation`, `TutorMessage`, `ExamDate`, `StudyPlan`, `StudyPlanItem`,
  `Achievement`, `UserAchievement`, `Streak`, `Notification`, `AuditLog`,
  `AIUsageLog`; role constants `ROLE_STUDENT/ADMIN/TEACHER/PARENT`, `ROLES`.
- `app/schemas.py` — auth + admin schemas (`SignupIn`, `LoginIn`, `TokenOut`,
  `UserOut`, `UserPage`, `AIUsageOut`, `AuditLogOut`, etc.); `Email` annotated type.
- `app/api/deps.py` — `get_current_user` (Bearer JWT + non-revoked `UserSession`
  jti + active user) and `require_admin`; legacy `get_current_student` was removed
  in increment 2 (see `current_student` above).
- `app/api/auth.py` — NEW: signup/login/refresh (rotating)/logout/me/patch me/
  password-reset request+confirm.
- `app/api/admin.py` — NEW: users list/search/get/patch/deactivate/reactivate,
  ai-usage, audit-logs (router-level admin guard; self-deactivation blocked).
- `app/services/audit.py` — NEW: `record_audit`.
- `app/config.py` — `MAX_UPLOAD_MB`, auth settings (`AUTH_SECRET_KEY`,
  `AUTH_ALGORITHM`, token expiries, `AUTH_EXPOSE_RESET_TOKEN`), bootstrap admin
  (`DEFAULT_ADMIN_EMAIL`/`PASSWORD`).
- `app/db.py` — `init_db()` calls `_ensure_bootstrap_admin()` (opt-in via env).
- `app/main.py` — registers `auth.router`, `admin.router`.
- `requirements.txt` — added `bcrypt>=4.2`, `PyJWT>=2.10`.
- `tests/` — `conftest.py` gains `test_session` (StaticPool) + `api_client`;
  `test_auth.py` NEW (~15 tests).


## What was built

### Design docs (`docs/`)
- `00-overview.md` — product vision, users, core loop, non-goals, success criteria.
- `01-architecture.md` — system shape, request lifecycles, config reference.
- `02-data-model.md` — entities, relationships, mastery update formula.
- `03-api-spec.md` — full HTTP contract.
- `04-ai-pipeline.md` — the five AI stages and prompt strategy.
- `05-roadmap.md` — phases, risks, definition of done.

### Backend (`backend/`) — FastAPI + SQLAlchemy + SQLite
- `app/main.py` — app factory, CORS, lifespan DB init, `/api/health`.
- `app/config.py` — env-driven settings; `app/db.py`, `app/models.py`,
  `app/schemas.py`.
- `app/llm/` — provider-agnostic interface:
  `base.py` (LLMProvider + JSON repair), `factory.py`, `openai_provider.py`,
  `anthropic_provider.py`, `ollama_provider.py`.
- `app/prompts/` — structuring, teaching, assessment, adaptive prompts.
- `app/services/` — `ingestion`, `structuring`, `teaching`, `assessment`,
  `adaptive`, `retrieval`, `pipeline`.
- `app/api/` — `materials`, `lessons`, `quizzes`, `sessions`, `deps`.
- `tests/` — 5 tests, no LLM required.
- `.env.example`, `requirements.txt`, `pytest.ini`.

### Frontend (`frontend/`) — React 19 + Vite + TS + Tailwind v4
- `src/api/client.ts` — typed API client.
- `src/components/` — `ui.tsx` (Card/Button/Spinner/Badge/ErrorText),
  `QuizRunner.tsx`.
- `src/pages/` — `MaterialsPage`, `MaterialDetailPage`, `LessonPage`,
  `QuizPage`, `StudyPage`.

## Verification evidence (last run)

- `backend`: `.\.venv\Scripts\python.exe -m pytest -q` → **88 passed** (auth +
  services + curriculum + repetition/reviews + tutor + planner/gamification/
  notifications + ai-usage + adaptive/assessment policy + seed; includes SM-2
  interval/lapse rules, due-queue filtering, quiz→mastery/history/review
  integration, owner scoping, grounded Socratic replies, verify persistence,
  cascade delete, provider-failure recovery, plan distribution and archiving,
  streak reset, achievement unlock, idempotent reminders, AI usage rows written
  with user/model/tokens and error status, the increment 9 `next_action`
  reteach/practice/advance/complete branches plus MCQ option-letter grading, and
  the increment 10 ingestion/retrieval embedding usage rows + seeded mastery
  history).
- `backend`: `python -c "import app.main"` → `import ok`.
- `frontend`: `npm run build` → **tsc typecheck + vite build succeeded**
  (270 modules transformed, dist emitted; includes the increment 7 admin console,
  increment 9/10 screens, and the increment 11 accessibility pass).
- `backend`: TestClient smoke test → health/upload/list/get/concepts/404/delete all
  correct, tables created via lifespan.

## Environment notes / gotchas

- **Python 3.14 only** on this machine. Two consequences already handled:
  - `numpy` has no cp314 wheel → dependency removed; cosine similarity is
    implemented in pure Python (`services/retrieval.py`).
  - Dependencies in `requirements.txt` use **loose lower bounds** for 3.14 wheel
    compatibility. Keep them loose unless you re-verify.
- **LLM calls are synchronous** (not async) to match the synchronous SQLAlchemy
  session model. If you add streaming later, introduce an async variant without
  changing service call sites.
- **No pnpm**; npm 11 is used.
- Corporate proxy caused intermittent PyPI download warnings; installs still
  succeed. Retry if a Python install fails.
- Default provider is **Ollama** (local). Nothing has been validated against a
  live LLM yet.

## Immediate next steps (v2 Core)

- [ ] Commit increments 1–6 once reviewed.
- [ ] **Validate the loop against a live provider** (Ollama locally, or OpenAI) —
      the pipeline logic has still not been exercised with a real model.
- [x] Increment 3 — spaced repetition + mastery v2 (`ReviewSchedule`, `MasteryEvent`).
- [x] Seed `MasteryEvent` history so demo data has a populated mastery timeline.
- [x] Increment 4 — Socratic tutor (`TutorConversation`/`TutorMessage`).
- [x] Increment 5 — planner + gamification + notifications.
- [x] Increment 6 — frontend app shell, feature screens, i18n + RTL, PWA.
- [x] Increment 7 — admin/AI-ops console (users, AI usage, audit).
- [x] Increment 8 — AI usage logging wired into the generation call sites.
- [x] Log embedding calls (ingestion + retrieval) too (`ingestion.embed`,
      `retrieval.embed`).
- [ ] Advanced tier — year rollover/tenancy, async streaming, richer analytics.
- [x] Add backend tests for `adaptive.next_action` policy and MCQ grading.
- [x] Harden list error/empty/loading states; `material.status` polling was already
      in place on the library + material detail screens.

See `docs/07-gap-analysis.md` for detail and `docs/05-roadmap.md` for phase framing.

## Resume checklist

1. Push the existing commit (authenticate first):
   ```powershell
   # create app password: https://bitbucket.org/account/settings/app-passwords/
   git push -u origin develpment
   ```
   Or switch to SSH if you prefer no password prompt.
2. Recreate the backend venv if it is missing:
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   Copy-Item .env.example .env
   ```
3. Frontend deps: `cd frontend; npm install`.
4. Run both: `uvicorn app.main:app --reload` and `npm run dev`.

## Open decisions

- Async vs streaming LLM path (deferred; sync for now).
- Real background worker vs FastAPI `BackgroundTasks` for processing.
- When to migrate SQLite → Postgres + pgvector.
