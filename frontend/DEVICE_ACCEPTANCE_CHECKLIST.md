# Device-by-device acceptance checklist

Use this checklist against the running app at the exact viewport widths below.
It defines acceptance criteria; checked items must be based on observed browser
behavior, not inferred from CSS alone. Record browser, OS, orientation, and date
when completing a release run.

## Current shell behavior to verify

- The app shell switches to compact bottom navigation below Tailwind's `sm`
  breakpoint (640px); the desktop navigation is shown at 640px and wider.
- Main content is capped at `max-w-6xl` (1152px) and gets wider side padding at
  the `sm` breakpoint.
- The global header remains sticky; the mobile bottom navigation is fixed and
  includes the device safe-area inset.
- The topic view uses horizontally scrollable tabs on narrow viewports and
  keeps one tab panel active at a time.

## 360px mobile portrait

- [ ] Landing, sign-in, library, material detail, topic, quiz, tutor, planner,
  settings, and notification screens have no horizontal page scroll.
- [ ] Header controls do not collide; bottom navigation labels/icons remain
  legible and do not obscure the last focusable content.
- [ ] Topic title, long lesson heading, objectives, markdown/code blocks, source
  excerpts, and errors wrap without clipping or forcing page-width overflow.
- [ ] All five topic tabs (Notes, Flashcards, Quiz, Tutor, Source) are reachable
  by touch and horizontal scroll; the active tab and its panel are announced.
- [ ] Flashcard flip, skip, Again/Good/Easy, quiz start, tutor send, and material
  back-link controls remain usable at 44px minimum target height.
- [ ] Tutor input and Send button fit together; typing and sending do not shift
  the page underneath the fixed navigation.
- [ ] Source excerpt text is readable; source index and relevance do not overlap.
- [ ] Keyboard focus is visible and can move through the tablist and active panel.
- [ ] Test both English LTR and Arabic RTL; tab scrolling and arrow/back labels
  remain understandable and do not cause horizontal page overflow.

## 768px tablet portrait

- [ ] Desktop header navigation is available at this width without wrapping into
  the main content or overlapping account/language controls.
- [ ] Topic tabs remain visible together when labels fit; if they overflow,
  horizontal scrolling still exposes Source and does not obscure focus.
- [ ] Lesson content and source excerpts use a readable line length; cards do not
  become edge-to-edge blocks with cramped internal padding.
- [ ] Flashcard and tutor actions remain touch-friendly; textarea and send action
  do not become too narrow.
- [ ] The fixed mobile bottom navigation is absent; no reserved bottom padding
  leaves an unexplained blank band.
- [ ] Validate 768px portrait and landscape separately; no clipped heading,
  lesson content, source reference, or sticky header controls.

## 1024px tablet landscape / compact laptop

- [ ] Header navigation and utility controls remain on a stable row or wrap
  cleanly without overlap.
- [ ] Topic body is centered and does not stretch past a comfortable reading
  measure; long source excerpts remain scannable.
- [ ] Tutor transcript and composer retain usable proportions; no horizontal
  scrolling is required to reach Send.
- [ ] Multiple lesson selectors wrap cleanly when titles are long.
- [ ] Keyboard navigation can traverse tabs, topic actions, and the current panel
  in a logical order.
- [ ] Test at 1024px both with English LTR and Arabic RTL.

## 1440px desktop

- [ ] Main content remains centered within the 1152px shell instead of stretching
  to the full viewport; no large, unbalanced empty columns appear.
- [ ] Topic notes, objectives, tutor responses, and source excerpts remain
  readable and grouped with their headings.
- [ ] Header navigation, language selector, notifications, profile, and sign-out
  remain visible without collision.
- [ ] Tab focus/selection is clear at keyboard focus and does not rely on color
  alone.
- [ ] The same content and interactions available on mobile remain available
  without accidentally displaying the mobile navigation.

## Cross-device functional and accessibility gates

- [ ] Every tab retains its function and data when switching between tabs.
- [ ] Topic route loads topic details by topic ID; lesson and quiz links use the
  associated lesson ID.
- [ ] Flashcard self-ratings update the backend review schedule; failures are
  visible and do not advance the card.
- [ ] Quiz generation, tutor conversation creation/message sending, and source
  loading show loading and error states.
- [ ] Source tab shows actual excerpt text returned by the API, or a clear
  no-linked-excerpts state; it never presents chunk IDs as if they were text.
- [ ] No keyboard traps; tablist uses tab/tabpanel semantics and has visible
  focus; reduced-motion preference is respected.
- [ ] PWA installability and offline behavior are checked separately in a
  production build; the development server is not evidence of PWA acceptance.

## Release record

| Date | Browser / OS | Viewports and orientations | Passed / failed | Issues |
|---|---|---|---|---|
| 2026-10-03 | Integrated browser, local Vite app with disposable seeded API data | 360, 768, 1024, 1440px; 900px-high viewport | Smoke checks passed for landing, sign-in, material-to-topic navigation, and authenticated topic view | Topic page had no horizontal document overflow at these widths; topic tabs were at least 44px high; mobile nav was visible at 360px and hidden at 768px+; ArrowRight moved focus/selection; source excerpt rendered; flashcard flip/rating and tab-state retention worked; tutor draft survived tab changes. Arabic, landscape, quiz generation, tutor send, PWA install, offline behavior, and other screens remain unverified. |

Release is blocked until each target viewport and the critical topic flow have
been exercised in a real browser. A successful TypeScript build alone does not
count as device acceptance.
