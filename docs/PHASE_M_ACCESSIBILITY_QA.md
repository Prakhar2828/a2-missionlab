# Phase M Accessibility + Mobile / Responsive QA

## Objective

Phase M is a bounded hardening pass over the completed Phase L public experience. It does not redesign protected mission simulations, alter mission evidence, replace the Phase K publication model, or compress desktop layouts into a generic mobile shell.

The Phase M product contract is:

- mobile navigation behaves as a keyboard-accessible disclosure and returns focus on Escape;
- visual selection state is also exposed to assistive technology;
- meaningful engineering canvases have an accessible name and a nearby text equivalent, while decorative canvas content remains hidden;
- nonessential canvas animation respects `prefers-reduced-motion` without disabling user-driven or mission-state simulation behavior;
- visible keyboard focus remains clear on the Windows viewer/lightbox and Mission Library controls;
- the Windows full-image action uses a native button rather than assigning button semantics to image content;
- existing safe-area, touch-target, typography, publication, and protected simulation contracts remain intact;
- responsive release QA covers the full Phase M viewport matrix in both Chrome and Edge before a production commit is accepted.

## Bounded production changes

### Shared navigation

`js/core.js` owns the disclosure behavior for the shared `.x-menu/.x-nav` and `.menu-btn/.nav-links` navigation systems. Opening and closing continues to use `aria-expanded`; Escape now closes an open mobile menu and returns focus to its trigger. Mission Library no longer installs duplicate navigation listeners.

`psi.html` intentionally remains independent of `core.js`, so `js/psi.js` receives the equivalent standalone disclosure behavior.

### Screen-reader state

Mutually exclusive visual button groups now synchronize `aria-pressed` state where appropriate:

- trajectory maneuver presets and direction controls;
- space-weather reference presets and mission-location context;
- PSI engine-count and regolith controls;
- GNC explanatory loop blocks (in addition to the already protected AUTO/MANUAL state).

Current-position controls use `aria-current` rather than `aria-pressed` when the semantic meaning is “where the user is now”:

- Entry event rail;
- Through Orion's Windows filmstrip.

Entry and Windows scrubbers expose richer `aria-valuetext` so the numeric slider value is paired with mission meaning.

### Canvas alternatives and reduced motion

The decorative landing-page star canvas remains `aria-hidden="true"`.

Meaningful engineering canvases expose `role="img"`, an accessible label, and either `aria-describedby` text or native fallback text. The descriptions point to the same visible mission interpretation already presented beside each visualization; no hidden alternate scientific claim is introduced.

Nonessential autonomous canvas motion is suppressed under `prefers-reduced-motion` in the shared landing hero and Mission Explorer. The canvas still redraws when state changes. User-driven or simulation-essential motion is not indiscriminately disabled: Entry playback and GNC progression remain explicit user-controlled engineering interactions, while PSI and Mission Control retain their existing reduced-motion handling.

### Windows semantics and focus

The current Artemis II image remains semantic image content with its descriptive `alt` text. A separate native `button` now owns the “open fullscreen” action and points to the existing dialog. This preserves the viewer geometry while avoiding `role="button"`/`tabindex` on the image itself.

Windows viewer/lightbox controls and Mission Library filters/cards retain clear `:focus-visible` outlines. Existing dialog Escape handling and focus restoration remain protected.

## Static Phase M gate

Run:

```text
python scripts/validation/validate_phase_m_accessibility.py
```

The static gate checks all eight public routes for language, main landmark, skip-link resolution, one primary H1, labeled navigation, image-alt presence, canvas semantics/text-equivalent references, native Windows image-action semantics, disclosure ownership, Escape/focus-return source contracts, screen-reader selected state, reduced-motion source contracts, visible focus contracts, safe-area support, the shared 44 px mobile control-height floor, and the protected Mission Control 64 px control contract.

## Expanded Chrome / Edge Phase M matrix

Run on Windows with both Chrome and Edge installed:

```text
python scripts/validation/validate_phase_m_regression.py
```

The browser gate exercises all eight routes at twelve viewport classes per browser:

1. 320 × 568
2. 360 × 800
3. 375 × 812
4. 390 × 844
5. 430 × 932
6. 844 × 390 phone landscape
7. 768 × 1024 tablet portrait
8. 1024 × 768 tablet landscape
9. 1024 × 800 approximately-1024 class
10. 1280 × 800
11. 1440 × 900
12. 1920 × 1080

That is 96 route/viewport cases per browser and 192 total cases. The gate checks unintended horizontal overflow, clipped interactive controls, zero-size canvas failures, route navigation completeness, mobile menu open/close state, Escape/focus return, link-close behavior, accessible control names, canvas naming, mobile control-height floors, selected-state ARIA contracts, Windows image semantics/current-filmstrip state, route-specific Windows/GNC/Mission Control invariants, and the existing responsive containment rules.

The pre-existing `validate_responsive_browser_qa.py` 96-case protected matrix remains unchanged and must still pass. Phase M adds coverage rather than weakening or replacing the protected suite.

## Protected regression gate

A Phase M release candidate must also pass the existing browser regressions for:

- Mission Explorer;
- Through Orion's Windows;
- GNC;
- Mission Control;
- PSI;
- Trajectory Correction;
- Space Weather;
- Entry / Descent / Recovery;
- Phase K publication behavior;
- Phase L typography behavior;
- the protected responsive matrix.

The analytical/evidence model validators for PSI, Trajectory, Space Weather, and Entry remain mandatory. `scripts/validate_public_experience.py`, text integrity, Phase K publication validation, and Phase L typography validation remain mandatory.

## Coverage boundary

The automated Phase M release gate is desktop Chrome + Edge driving responsive emulation. That is not equivalent to a physical-device pass. Do not claim iPhone Safari, Android Chrome, tablet hardware, or desktop Safari coverage unless those devices/browsers are actually run. Those remain manual release-candidate targets for Phase P.
