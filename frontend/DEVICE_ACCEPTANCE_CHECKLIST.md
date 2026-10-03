# Device-by-device acceptance checklist

This checklist defines the required screen-level acceptance criteria for the Suhail Smart Teacher Platform. It is intentionally stricter than basic responsiveness and is meant to validate actual mobile, tablet, and desktop behavior before release.

## Device targets
- 360px mobile
- 768px tablet
- 1024px tablet/laptop
- 1440px desktop

## Escape criteria
A screen passes only when all items in the relevant section pass without broken layout, content clipping, blocked controls, or inaccessible interactions.

## 360px mobile checklist
- [ ] Public landing page loads cleanly and fits within the viewport without horizontal scroll.
- [ ] Auth screen keeps form fields fully readable and interactive with no clipped labels or controls.
- [ ] Core action buttons remain at least 44px tall and easy to tap with one hand.
- [ ] Navigation is accessible via a mobile bottom nav or equivalent compact control pattern.
- [ ] The main content avoids overlap with fixed navigation and safe-area insets.
- [ ] Language switching and all primary actions remain reachable without requiring zoom.
- [ ] Focus styles are visible and consistent for keyboard and assistive-tech users.
- [ ] No content is hidden under sticky headers or floating bars.
- [ ] Offline shell fallback loads with the app still usable when the network is unavailable.
- [ ] The app remains readable in both English and Arabic without broken alignment or RTL reversal issues.

## 768px tablet checklist
- [ ] Layout adapts to a tablet reading width without large empty gutters or cramped content blocks.
- [ ] Cards and forms maintain comfortable spacing and readable line lengths.
- [ ] Navigation remains clear without overcrowding the header or causing content wrap issues.
- [ ] Learning and dashboard information are easy to scan in portrait and landscape orientations.
- [ ] RTL Arabic layout remains visually balanced and readable without mirrored text glitches.
- [ ] Touch targets remain comfortably sized for tablet interactions.
- [ ] PWA offline fallback remains functional and consistent with mobile behavior.

## 1024px tablet/laptop checklist
- [ ] Dashboard and library views remain balanced and legible at this intermediate width.
- [ ] Multi-column content does not force excessive scanning or clumsy alignment.
- [ ] Secondary actions remain visible without crowding core content.
- [ ] Tutor, planner, and review screens maintain readable spacing and clear flow.
- [ ] Edge cases such as long titles, status badges, and compact tables remain usable.
- [ ] Accessibility landmarks and focus order remain clear across the wider viewport.

## 1440px desktop checklist
- [ ] Wide layouts use space efficiently without excessive empty gaps or stretched single-column designs.
- [ ] Dashboard, admin, and analytics screens remain legible and visually grouped.
- [ ] Dense information is still readable and scannable without overwhelming the user.
- [ ] Navigation and utility actions retain clarity when the viewport is wide.
- [ ] PWA state, loading, and offline support continue to behave predictably across desktop browsers.

## Accessibility and quality gates
- [ ] Skip links and landmark navigation remain available at all sizes.
- [ ] Heading hierarchy stays valid and consistent across screens.
- [ ] Color contrast is passable in light and dark states used by the app shell.
- [ ] Reduced-motion preferences are respected.
- [ ] Input labels are fully visible and associated correctly.
- [ ] Forms remain usable with keyboard-only navigation.

## Release requirement
The app is not release-ready until all checklist items pass at the required widths for the planned user flows and the critical screens have been manually validated in a browser/device matrix.
