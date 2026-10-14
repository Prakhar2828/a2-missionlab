# A2 MissionLab Release Quality Standard

This document defines the minimum acceptance bar for the public experience.

The standard is intentionally stricter than "the page loads" or "the existing
validator passes." Every route and every interaction is treated as a
release-critical product surface.

## 1. Evidence and scientific integrity

- NASA-reported facts, MissionLab-derived values, models, inferences, and
  unknown/not-public information remain visibly distinct.
- Presentation changes must not silently change validated mission facts,
  mission timing, derived geometry, model assumptions, or evidence labels.
- Educational interpolation or visualization must never be presented as
  private telemetry.
- Future-Artemis engineering topics must remain explicitly separated from the
  flown Artemis II record.

## 2. Text and source integrity

- All public web source files must be valid UTF-8 without a BOM.
- No replacement characters, mojibake, broken arrows, broken multiplication
  signs, or placeholder question-mark glyphs are allowed.
- Public titles, metadata, controls, labels, units, and symbols must render
  intentionally.
- External links opened in a new tab must use noopener noreferrer.

## 3. Layout invariants

- No route may create horizontal document overflow at the supported viewport
  matrix.
- Discrete navigation inside a fixed experience must not move the user's page
  position unless the interaction explicitly requests navigation.
- Mission Explorer and Windows slide navigation target no more than 1 px of
  unintended change in page scroll position and stable-stage top/height.
- Critical data, controls, labels, and explanatory text may not overlap or be
  obscured by decorative overlays.
- Variable content must be contained by deterministic layout regions rather
  than resizing the entire interaction unpredictably.

## 4. Interaction quality

- Every visible control must perform a meaningful action.
- Buttons use explicit button types and controls have accessible names.
- Primary touch targets must be at least 44 x 44 CSS pixels on phone layouts.
- AUTO demonstrations must make useful visible progress immediately and
  complete within 25 seconds under normal supported-device conditions.
- Simulation time must not slow down merely because rendering frame rate drops.
- Reduced-motion preferences must be respected for non-essential animation.

## 5. Responsive/browser matrix

Required representative viewports:

- 390 x 844
- 430 x 932
- 768 x 1024
- 844 x 390
- 1366 x 768
- 1440 x 900

Automated Chromium-family coverage is necessary but not sufficient.

Before production release, the candidate must also be checked on real:

- iPhone Safari, portrait and landscape
- Android Chrome, portrait and landscape
- tablet Safari/Chrome
- macOS Safari

## 6. Performance and resilience

- Canvas simulations use elapsed time correctly and remain stable under frame
  rate variation.
- Long-running animation loops may not leak duplicate listeners or runtimes
  after resize/navigation.
- Non-critical imagery should not block interaction readiness.
- Missing remote imagery must degrade to the local fallback without breaking
  layout.
- No uncaught JavaScript exceptions or console-error floods are accepted.

## 7. Accessibility

- Exactly one page-level H1 is expected per public route.
- Images require an intentional alt attribute.
- Inputs require an associated label or aria-label.
- Canvas surfaces require an accessible label or must be explicitly hidden.
- Keyboard focus, Escape behavior, dialogs, mobile navigation, and reduced
  motion must remain usable.

## 8. Release gate

A release candidate is not accepted until all applicable checks are green:

1. git diff --check
2. JavaScript syntax checks
3. Python compilation
4. public text/markup integrity
5. public experience validation
6. publication/release validation
7. Windows no-scroll regression
8. responsive Edge/Chrome browser matrix
9. phase-specific interaction regressions
10. human visual inspection on the real-device matrix

A validator passing is evidence that a defined invariant passed. It is never
treated as proof that the entire user experience is polished.
