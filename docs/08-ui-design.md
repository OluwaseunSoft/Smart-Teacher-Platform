# Student interface

The student shell and dashboard follow `SuhailDashboard_2.html`: navy surfaces,
blue and teal accents, rounded cards, and a sidebar with clear icon-and-text
navigation. Dark appearance is the default. The header offers a light appearance;
the choice is saved locally as `suhail.theme`. Shared cards, controls, and lesson
content follow the selected appearance across authenticated screens.

Typography uses the reference's friendly heading direction: locally available
Baloo 2, followed by Trebuchet MS, Gill Sans, and Candara. Body text uses Nunito
when installed, followed by Segoe UI and Tahoma. Fonts require no network request.
Navigation and dashboard icons are consistent decorative SVGs with adjacent text
or accessible button labels.

For learners aged 9–22, the dashboard emphasizes one next step, plain instructions,
and personal progress. Streaks and achievements support encouragement without
rankings or competitive pressure. Metrics come from the existing dashboard API;
empty states explain how to start instead of showing invented activity.

Desktop navigation stays visible. Below 768px, Home/Dashboard, Library, Tutor,
and Reviews appear in a bottom bar; More opens Upload, Planner, Progress,
Settings, and Sign out (plus Admin for administrators). The menu moves focus to
its first link, closes on Escape or an outside click, and returns focus to its
trigger when dismissed with Escape. Touch targets are at least 44px.

New dashboard text is available in English and Arabic. Logical CSS properties
mirror the layout in RTL, directional arrows reverse, and numeric ratios retain
their reading order. Reduced-motion preferences disable animated transitions.

## Arabic translation and content alignment

Use locally managed English/Arabic strings in `frontend/src/i18n.tsx` for
interface labels; these are deterministic and need no AI call. Educational
content uses the existing authenticated `POST /api/translate` endpoint for
dynamic AI translation. The notes screen exposes translation of a summary to
Arabic. English technical terms are retained in brackets by the translation
prompt. This requires the configured generation provider to be available.

Uploaded Arabic text does not need translation to display correctly. Markdown
paragraphs, headings, list items, and quotations resolve their own direction
with `dir="auto"`; CSS `:dir(rtl)` explicitly aligns them right, and `:dir(ltr)`
aligns English blocks left. This is independent of the interface language.
Plain-text summaries, source excerpts, and flashcards follow the same rule.
Code blocks retain LTR rendering. AI translations render as Markdown so their
paragraph breaks and per-block direction are preserved.

Validation from `frontend/`:

```powershell
npm run typecheck
npm run build
npm exec -- vitest run --maxWorkers=1
```

With Vite running on `http://127.0.0.1:5173`, run
`node scripts/browser-check.mjs` for an isolated Chrome smoke check. It uses API
fixtures, checks layouts, navigation, themes, and RTL, and writes screenshots to
a temporary directory. `CHECK_URL` and `CHROME_PATH` override the defaults.
