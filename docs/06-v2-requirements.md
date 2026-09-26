# Suhail Smart Teacher — v2 Consolidated Requirements

> Status: **authoritative requirements for v2.** Supersedes the MVP framing in
> `00-overview.md` where they conflict. Preserves the original platform vision but
> expands scope to a multi-user, bilingual, role-based product.
>
> Tiering legend used throughout:
> - **Core** — must be built for v2 to be complete.
> - **Advanced** — build if time allows; designed-for but may ship later.
> - **Stretch** — explicitly deferred; architecture must not block it.

---

## 1. Document purpose

This document consolidates the v2 product specification into a single source of
truth: problem, users, roles, functional features, screens, data/API expectations,
non-functional requirements, test scenarios, evaluation rubric, and explicit
out-of-scope items. It is the reference for implementation and acceptance.

---

## 2. Product definition

### 2.1 Problem

- Students (Grades 7–12) have raw study material (textbooks, notes, PDFs) but lack
  structure and a personal teacher to guide them.
- Generic AI chatbots answer isolated questions but do not build, remember, or
  sequence a curriculum, and do not adapt to a student over time.
- Existing study apps are static (flashcards/PDFs) or generic, with no adaptive loop
  and little support for Arabic/RTL learners.

### 2.2 Solution

An AI-powered learning platform that behaves like a personal teacher:

1. **Reads** uploaded material (PDF, text, notes).
2. **Organizes** it into a structured curriculum (Subject → Chapter → Topic).
3. **Teaches** it adaptively and conversationally (Socratic tutor).
4. **Tests** understanding with generated assessments.
5. **Adapts** to each student via explicit, computed mastery and spaced repetition.
6. **Plans** study around exam dates and available time.
7. **Motivates** with gamification (streaks, achievements).

### 2.3 Objectives

- Deliver a coherent upload → organize → teach → test → adapt loop.
- Provide secure multi-user accounts with server-enforced ownership (US-12).
- Be fully bilingual **Arabic/English** with correct **RTL** layout.
- Be **mobile-first** and installable as a **PWA**.
- Ground all generated content in retrieved source chunks to reduce hallucination.
- Keep the AI provider swappable (OpenAI / Anthropic / Ollama) via config only.

### 2.4 Target audience

- **Primary:** Students, Grades 7–12 (bilingual AR/EN).
- **Secondary (roles):** Administrators (Core), Teachers and Parents (Stretch).
- Multi-tenancy ready (schema supports institution/school scoping) even if single
  tenant at launch.

### 2.5 Design principles

- **Adaptation is explicit, not vibes.** Mastery is a computed number; next-step
  policy is deterministic and testable; the LLM only phrases output.
- **Ground everything.** Lessons/quizzes cite retrieved source chunks.
- **Accessibility first.** WCAG-aware, keyboard navigable, screen-reader labels.
- **Mobile-first.** Design small screens first; scale up.
- **Arabic is not an afterthought.** True RTL, not mirrored CSS hacks.
- **Fail gracefully.** Provider outages produce clear, recoverable states.
- **Privacy by default.** Student data is private; access is ownership-checked.

### 2.6 Success metrics

- A student completes the full loop without leaving the app.
- Processing survives a provider outage (clear error states, retry).
- Ownership is enforced server-side on every student-scoped endpoint.
- Arabic and English both render correctly (including RTL).
- Switching AI provider requires only a config change.
- The app runs locally with two commands (backend + frontend).

---

## 3. Roles, personas, and user stories

### 3.1 Roles

| Role | Tier | Description |
|---|---|---|
| Student | Core | Owns material, lessons, quizzes, plans, progress. |
| Administrator | Core | Manages users, content, AI operations, audit. |
| Teacher | Stretch | Assigns material to classes; reviews progress. |
| Parent | Stretch | Views a child's progress/read-only summaries. |

### 3.2 User stories

- **US-01** As a student, I can register and log in securely.
- **US-02** As a student, I can upload PDFs/text and have them processed.
- **US-03** As a student, I can see my material organized into subjects/chapters/topics.
- **US-04** As a student, I can read/hear a lesson for a topic.
- **US-05** As a student, I can take a quiz and get scored with feedback.
- **US-06** As a student, I can ask the Socratic tutor questions and get guided help.
- **US-07** As a student, I can review with spaced repetition (flashcards/review queue).
- **US-08** As a student, I can set an exam date and get a study plan.
- **US-09** As a student, I can track streaks and achievements.
- **US-10** As a student, I can use the app in Arabic or English with correct RTL.
- **US-11** As an admin, I can manage users (list/search/deactivate) and view AI usage.
- **US-12** As a user, I can only access my own data (server-enforced authorization).
- **US-13** As a student, I receive notifications/reminders for reviews and plans.

---

## 4. Functional features

Each feature is tagged with its tier. **Core** is required for v2 acceptance.

### A. Accounts & Authentication — Core

- Email + password registration and login.
- Password hashing (bcrypt); never store plaintext.
- JWT access tokens; server-side session records for revocation/logout.
- Refresh flow and logout; password reset hooks.
- Profile: display name, grade, preferred language, timezone.

### B. Roles & Authorization — Core

- Role model (Student, Administrator; Teacher/Parent reserved for Stretch).
- Dependency guards: `get_current_user`, `require_admin`.
- Ownership enforcement on every student-scoped resource (US-12).
- Admin-only endpoints for user management.

### C. Material ingestion — Core

- Upload PDF, plain text, and pasted notes.
- Extract text, chunk, and store source documents + chunks.
- Processing status with clear error states; retry on failure.

### D. Curriculum structuring — Core

- Build hierarchy: **Subject → Chapter → Topic**.
- Map topics to source chunks (grounding).
- Deterministic ordering (chapter order, topic order).

### E. Adaptive teaching — Core

- Generate a lesson per topic, grounded in retrieved chunks.
- Read and (where available) listen (TTS) to lessons.
- Adapt explanation based on mastery.

### F. Assessment — Core

- Generate quizzes (MCQ + short answer) per topic.
- Grade and give feedback; update mastery.
- Deterministic next-step policy: reteach / practice / advance.

### G. Socratic tutor — Core

- Conversational, guiding (not answer-dumping) tutor per topic.
- Persist conversations/messages for continuity.
- Ground answers in source chunks.

### H. Spaced repetition — Core

- Review schedule per topic/concept (SM-2-like intervals).
- Review queue surfacing due items.
- Update intervals based on recall performance.

### I. Study planner — Core

- Set exam date and study availability.
- Generate a plan distributing topics before the exam.
- Track plan progress.

### J. Gamification — Core

- Streaks (daily activity), achievements/badges.
- Progress dashboards (mastery, coverage).

### K. Notifications — Core

- In-app notifications/reminders (review due, plan tasks).
- (Email via test service acceptable; production-scale email out of scope.)

### L. Bilingual AR/EN + RTL — Core

- UI language switch; content language preference.
- Correct RTL layout for Arabic.
- Localized labels/messages.

### M. Mobile-first / PWA — Core

- Responsive, mobile-first layouts.
- Installable PWA (manifest + service worker; offline shell where feasible).

### N. Accessibility — Core

- WCAG-aware semantics, keyboard navigation, ARIA labels, focus management.
- Sufficient contrast; respects reduced motion.

### O. Admin & AI operations — Core

- User management (list/search/deactivate/reactivate).
- AI usage log (provider, tokens, latency, errors).
- Audit log for sensitive actions.

### P. Year rollover & tenancy readiness — Advanced

- Academic year entity; rollover/archiving.
- Institution/school scoping on entities for future multi-tenancy.

---

## 5. Required screens (Core unless noted)

1. Landing / marketing page.
2. Sign up.
3. Log in.
4. Forgot / reset password.
5. Onboarding (grade, language, subjects).
6. Student dashboard (progress, streak, due reviews, next step).
7. Material upload & processing status.
8. Material detail (structured curriculum).
9. Lesson view (read + listen, grounding references).
10. Quiz runner (question → answer → feedback → score).
11. Tutor chat (Socratic).
12. Review queue (spaced repetition / flashcards).
13. Study planner (exam date, plan, progress).
14. Progress / achievements.
15. Notifications center.
16. Admin console (users, AI usage, audit).
17. Settings / profile (language, RTL, account).

---

## 6. Data model & API expectations

### 6.1 Core entities

- **User** (id, email, password_hash, role, display_name, grade, language,
  timezone, is_active, timestamps).
- **Session** (id, user_id, token/jti, issued_at, expires_at, revoked_at, user_agent).
- **StudentProfile** (user_id, preferences, streak counters).
- **AcademicYear** (Advanced; id, label, start/end, is_active, institution_id).
- **Institution** (Advanced/tenancy-ready; id, name).
- **Subject → Chapter → Topic** hierarchy (topic maps to source chunks).
- **SourceDocument** (uploaded material) → **SourceChunk** (retrievable text).
- **Lesson** (topic_id, content, language, grounding refs).
- **Quiz → Question → Attempt → Answer** (scores, mastery deltas).
- **MasteryState** (per user × topic; computed score + history).
- **ReviewSchedule** (per user × topic; interval, due_at, ease, reps/lapses).
- **TutorConversation → TutorMessage** (personalized, grounded).
- **ExamDate / StudyPlan → StudyPlanItem**.
- **Achievement / UserAchievement / Streak**.
- **Notification**.
- **AuditLog** (actor, action, target, metadata, timestamp).
- **AIUsageLog** (provider, model, tokens, latency, status, error).

### 6.2 API expectations

- Versioned under `/api`; auth under `/api/auth`.
- Bearer-token authentication; 401 unauthenticated, 403 unauthorized.
- Student-scoped resources never allow cross-user access.
- Admin endpoints under `/api/admin` with `require_admin`.
- Consistent error envelope and status codes.
- All list endpoints paginate.
- Provider-agnostic AI behind one interface.

---

## 7. Non-functional requirements

- **Security/privacy/safety:** bcrypt hashing, JWT + revocable sessions, ownership
  checks, input validation via Pydantic, no secrets in logs, safe handling of
  uploaded files, content safety guardrails for minors.
- **Performance:** responsive interactions; processing is background/long-running
  with status polling.
- **Reliability:** graceful provider-outage handling; retries; clear errors.
- **Portability:** SQLite for local/dev; schema Postgres-compatible; provider swap
  by config.
- **Internationalization:** AR/EN with RTL; language stored per user.
- **Accessibility:** WCAG-aware as in §4N.
- **Observability:** AI usage logs, audit logs, health endpoint.
- **Maintainability:** typed interfaces, tests, docs, meaningful commits.

---

## 8. Test scenarios (acceptance)

1. Register → login → access dashboard.
2. Unauthenticated request to a protected endpoint → 401.
3. Student A cannot read/write Student B's material → 403/404.
4. Admin can list/search/deactivate users; non-admin cannot.
5. Upload PDF → processing → structured curriculum appears.
6. Lesson generated and grounded in source chunks.
7. Quiz scores correctly; mastery updates; next-step chosen.
8. Socratic tutor guides rather than dumps answers; conversation persists.
9. Review queue surfaces due items; intervals update after review.
10. Exam date → study plan generated and tracked.
11. Streak increments on daily activity; achievement unlocks.
12. Language switch to Arabic renders RTL correctly.
13. Provider outage shows clear error state and allows retry.

---

## 9. Evaluation rubric (weights)

| Area | Weight |
|---|---|
| Functionality / completeness | 25% |
| Architecture / code quality | 20% |
| AI integration & learning design | 15% |
| Security / privacy / safety | 15% |
| UX / responsiveness / accessibility / Arabic | 15% |
| Testing / docs / commits | 10% |

---

## 10. Out of scope

- Native mobile apps (responsive web/PWA only).
- Payments / billing.
- Live video / real-time collaboration.
- Official curriculum content (users supply their own material).
- Production-scale email (test service acceptable).
- Handwriting/OCR of images (PDF text layer only).

---

## 11. Tiering summary

- **Core:** A–O (auth, roles/authz, ingestion, structuring, teaching, assessment,
  tutor, spaced repetition, planner, gamification, notifications, bilingual/RTL,
  mobile/PWA, accessibility, admin/AI-ops).
- **Advanced:** P (year rollover, tenancy readiness) + async/streaming lesson
  generation + richer analytics.
- **Stretch:** Teacher/Parent roles, class assignments, institution dashboards,
  pgvector/Postgres migration at scale.
