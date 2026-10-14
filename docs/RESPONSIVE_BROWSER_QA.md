# A2 MissionLab Responsive and Browser QA

Phase I validates the full public experience across a deterministic desktop
browser matrix and records the remaining true-device shipping checks.

## Automated matrix

Browsers:

- Microsoft Edge
- Google Chrome

Routes:

1. `index.html`
2. `mission.html`
3. `windows.html`
4. `gnc.html`
5. `mission-control.html`
6. `library.html`
7. `technical-report.html`

Viewport profiles:

- 390 x 844
- 430 x 932
- 768 x 1024
- 844 x 390
- 1366 x 768
- 1440 x 900

Each browser executes 42 route/viewport cases, for 84 automated cases total.

Automated checks include:

- page-level horizontal overflow
- clipped interactive controls
- permanent route navigation
- mobile-menu opening and closing
- canvas geometry
- Through Orion's Windows image-control containment
- GNC primary touch-target dimensions
- Mission Control scenario availability
- route-specific DOM contracts

## True-device shipping gate

Windows headless Chromium cannot truthfully certify actual iOS Safari,
Android browser chrome behavior, or macOS Safari rendering.

Before production deployment, check the final published candidate on:

### iPhone Safari

Test portrait and landscape.

Confirm:

- no horizontal page overflow
- mobile navigation opens and closes
- landing page remains readable
- Mission Explorer remains usable
- Windows arrows do not vertically move the page
- Windows fullscreen viewer respects safe areas
- pinch, pan, double tap, swipe, reset, and close work
- metadata does not cover the photograph
- GNC AUTO and MANUAL remain reachable
- GNC sensor/state labels do not overflow
- Mission Control explanatory text remains readable
- controls are not hidden behind browser chrome or the home indicator

### Android Chrome

Repeat phone portrait and landscape checks, including dynamic browser-chrome
resize behavior.

### Tablet Safari / Chrome

Check portrait and landscape transitions, simulators, navigation, cards, and
control panels.

### macOS Safari

Check every permanent route and the Windows immersive viewer.

## Evidence boundary

Responsive QA changes presentation and browser validation only. It must not
change mission facts, mission timing, trajectories, evidence classifications,
public-data boundaries, or the distinction between onboard navigation state,
ground orbit determination, and public trajectory products.
