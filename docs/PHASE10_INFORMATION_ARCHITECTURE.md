# Phase 10 — Public Experience Rearchitecture

## Status

Architecture locked before implementation.

Production baseline:

718abc5e18403ba26eff3a68cfd208690ce6dbaf

Implementation branch:

phase-10-experience-rearchitecture

---

## Goal

Transform A2 MissionLab from one long scrolling public page into a focused multi-page mission experience while preserving:

- public-data-only evidence discipline
- all validated technical results
- all 25 Through Orion's Windows mission moments
- all 28 Mission Library deep dives
- the Technical Report
- desktop and mobile behavior
- accessibility
- GitHub Pages static deployment
- current validation and release guardrails

---

## Public Information Architecture

### 1. index.html — Landing Experience

Purpose:

Introduce A2 MissionLab quickly and direct visitors toward the experience that best matches their intent.

Keep:

- cinematic Artemis II hero
- concise project explanation
- selected mission metrics
- compact mission photography strip
- high-level capability and methodology summary
- selected experience cards
- links to technical depth

Remove from homepage:

- full Mission Explorer
- full 25-image gallery
- full GNC simulator
- full Mission Control simulator
- full Entry simulator
- full trajectory-correction lab
- full Space Weather simulator
- future-Artemis PSI simulator

Primary CTA:

Explore the Mission → mission.html

Secondary CTA:

Read the Technical Report → technical-report.html

---

### 2. mission.html — Mission Explorer

Primary mission-story destination.

Contains:

- Mission Explorer timeline
- mission geometry visualization
- mission milestones
- trajectory-correction lab
- atmospheric Entry / Descent / Recovery experience
- Space Weather mission-operations context
- engineering drawers relevant to those experiences

Purpose:

Move a visitor through Artemis II chronologically while connecting orbital mechanics, corrections, environment, and return.

---

### 3. windows.html — Through Orion's Windows

Dedicated visual and science experience.

Contains:

- all 25 current curated mission moments
- current evidence labels and provenance
- current NASA source links
- geometry context
- image timeline
- arrow navigation
- keyboard navigation
- thumbnails
- engineering drawer

Phase 10 upgrades:

- stable viewer geometry with zero page jump
- desktop fixed viewer region
- mobile fixed viewer region
- fade transitions
- image preloading
- zoom and lightbox
- stronger premium photo-browser presentation
- no unnecessary vertical movement during navigation

No image or evidence item may be dropped during extraction.

---

### 4. gnc.html — Guidance, Navigation & Control

Contains:

- proximity-operations teaching model
- AUTO mode
- MANUAL mode
- disturbance injection
- translation and rotation controls
- sensor and state-product explanations
- Sense → Estimate → Guide → Control → Fire → Verify loop
- public evidence boundaries
- engineering drawer

Purpose:

Give GNC enough room to feel like an actual focused interactive lab instead of one section in a long webpage.

---

### 5. mission-control.html — Mission Control

Contains:

- Flight Director framing
- discipline guide
- event scenarios
- console perspectives
- evidence-aware decision traces
- Mission Control canvas
- decision-reconstruction engineering material

Purpose:

Make the Mission Control experience self-contained and intuitive to visitors unfamiliar with flight-control roles.

---

### 6. library.html — Mission Library

Preserve existing technical knowledge base.

Requirements:

- retain all 28 validated topics
- retain search
- retain all evidence boundaries
- retain all figure references
- improve navigation only where needed

This page is already structurally appropriate and should not be rebuilt unnecessarily.

---

### 7. technical-report.html — Technical Report

Preserve the current report as the deepest formal documentation layer.

Requirements:

- retain all validated sections
- retain evidence terminology
- retain equations
- retain provenance
- retain reproducibility discussion

Only navigation and presentation integration should change unless a later audit finds an actual problem.

---

## Global Navigation

Desktop and mobile navigation:

1. Mission
2. Windows
3. GNC
4. Mission Control
5. Library
6. Technical Report

Brand:

A2 MissionLab → index.html

Navigation must be page-based.

Do not use homepage hash anchors as the primary navigation architecture.

---

## Evidence Model

The following classifications remain permanent:

- NASA REPORTED
- MISSIONLAB DERIVED
- MODELED
- INFERRED
- UNKNOWN / NOT PUBLIC

Page extraction must never blur these boundaries.

---

## JavaScript Architecture

The existing app.js is not safe for direct multi-page use because it currently exits when #mission-canvas is missing.

Target structure:

js/
  core.js
  mission.js
  windows.js
  gnc.js
  mission-control.js

core.js owns:

- DOM helpers
- viewport handling
- responsive canvas runtime
- shared drawing utilities
- common navigation
- shared image fallback behavior
- accessibility and common interaction helpers

Each experience file initializes independently only when its relevant DOM exists.

There must be no page-level dependency requiring another experience's canvas to exist first.

---

## CSS Architecture

Do not rewrite the entire stylesheet at once.

Preserve:

- styles.css
- responsive-hardening.css

until extraction is stable.

New page-specific CSS may be added incrementally after behavior is preserved.

The existing mobile Safari and iPhone hardening is considered production-tested behavior and must not be discarded casually.

---

## Gallery Stability Requirement

The Through Orion's Windows viewer must maintain stable geometry while switching slides.

Regression invariant:

For each navigation action:

- record window.scrollY
- record viewer getBoundingClientRect().top
- navigate forward or back
- wait for the viewer update
- assert both values remain within an agreed small tolerance

Image aspect ratio, metadata length, title length, and description length must not cause the overall page position to move.

---

## Responsive Validation Matrix

Required viewport classes:

- desktop
- compact laptop
- tablet portrait
- tablet landscape
- narrow Android-class phone
- modern iPhone-class phone
- short landscape phone

At minimum test representative widths around:

- 1440 px
- 1180 px
- 1024 px
- 768 px
- 430 px
- 390 px
- 360 px

---

## Visual Direction

Preserve the current dark MissionLab identity.

Target improvements:

- stronger hierarchy
- more whitespace
- larger photography
- fewer simultaneous UI panels
- cleaner navigation
- restrained animation
- consistent cards and drawers
- professional aerospace mission-storytelling feel

Avoid:

- generic SaaS dashboard styling
- excessive gradients
- decorative clutter
- unnecessary pills
- every section looking like a separate demo
- rebuilding proven responsive behavior without need

---

## Celestial-Body Rendering

Current procedural Earth and Moon drawings are acceptable for schematic diagrams but not for cinematic simulation scenes.

Phase 10 should distinguish between schematic and physical presentation.

### Schematic mode

Allowed:

- simple circles
- state diagrams
- explanatory geometry

### Physical / cinematic mode

Use:

- verified NASA or public-domain Earth texture or imagery
- verified NASA or public-domain lunar texture or imagery
- realistic lighting and limb treatment
- subtle atmosphere where appropriate

Do not claim visual fidelity beyond the underlying model.

---

## Validation Contract

Existing validation may change in structure but not in strength.

The current validator assumes all interactive IDs live in index.html.

Phase 10 must convert that requirement into a page-aware contract.

Expected interaction ownership:

mission.html
  mission-canvas
  mission-scrubber
  entry-canvas
  entry-scrubber
  maneuver-canvas
  dv-magnitude
  weather-canvas

windows.html
  crew-photo
  crew-scrubber
  crew-geometry-canvas
  crew-image-prev
  crew-image-next
  crew-image-count

gnc.html
  gnc-canvas
  gnc-start
  gnc-mode-auto
  gnc-mode-manual
  gnc-disturbance
  gnc-autopilot-status

mission-control.html
  mc-canvas

Validators must continue to confirm:

- 25 Through Orion's Windows moments
- at least 28 Mission Library topics
- Technical Report coverage
- required evidence terminology
- local asset integrity
- repository dependencies
- no forbidden overclaims
- final release boundaries

---

## Implementation Sequence

### Phase C

Refactor JavaScript into independent runtimes without changing the public page structure.

### Phase D

Create destination pages and move experiences out of the homepage.

### Phase E

Rebuild landing page and global navigation.

### Phase F

Fix gallery geometry and add automated scroll-position regression tests.

### Phase G

Polish each dedicated simulator page.

### Phase H

Upgrade physical and cinematic Earth and Moon visuals using verified public assets.

### Phase I

Complete responsive and browser QA.

### Phase J

Run full regression validation, update release documentation, commit final architecture, and prepare deployment.

---

## Non-negotiable Rule

Architecture changes may reorganize presentation and code ownership.

They may not change validated mission facts, derived results, evidence classifications, or scientific conclusions unless a separate evidence review explicitly justifies that change.
