# A2 MissionLab — Final Public Experience Polish Overlay

This package is the final public-experience polish layer for the existing `a2-missionlab` repository. Extract it over the repository root on the `public-experience-v3` working branch. It does **not** delete or replace validated Phase 0–9 data pipelines, source datasets, or analysis code.

## Final release profile

- preserves the V4 cinematic dark / Mission Control visual identity
- includes the final publish-readiness overlap fixes and site-wide readability pass
- preserves NASA-reported vs MissionLab-derived vs modeled vs unknown evidence boundaries
- expands **Through Orion's Windows** to 25 provenance-labeled Artemis II moments
- adds in-image gallery arrows, keyboard navigation, a counter, timeline, scrubber, and rapid filmstrip browsing
- removes the distracting interior Orion-window bars while retaining the subtle outer window frame
- adds GNC **AUTO MODE**, **MANUAL MODE**, and **Introduce disturbance** in both modes
- rebuilds the GNC loop presentation and public GNC / navigation diagrams for clean arrows and readable state-estimate content
- adds a Mission Control role explainer and distinguishes official role context from MissionLab shorthand / synthesis lenses
- strengthens trajectory-correction feedback without turning the teaching model into a false high-fidelity simulation
- makes Space Weather outputs operationally legible to non-experts
- separates PSI plume **cant** (direction) from plume **spread** (width) and explains why both matter
- keeps the Technical Report and Mission Library depth layers intact
- retains the explicit statement that Artemis II did **not** land on the Moon
- retains current NASA campaign context: Artemis III is a 2027 LEO demonstration and Artemis IV targets the first Artemis lunar landing in early 2028

## Evidence rules retained

- NASA reported fact ≠ MissionLab derived result
- modeled quantity ≠ telemetry
- public trajectory product ≠ Orion onboard navigation state
- sequence ≠ causation
- troubleshooting action ≠ confirmed root cause
- discipline relevance ≠ decision ownership
- mission image ≠ exact reconstructed instant unless metadata supports it
- unknown public fact ≠ permission to invent

## Validation

Run from the repository root after extracting this overlay:

```powershell
python scripts\validate_public_experience.py
```

That is the authoritative full-repository check because it can inspect the existing dependencies under `data/`, `docs/assets/`, and `scripts/`.

To validate this overlay package by itself:

```powershell
python scripts\validate_public_experience.py --overlay-only
```

The final-polish package itself passes overlay validation. Build-environment QA details are recorded in:

```text
validation/public-experience-final-polish/BROWSER_VALIDATION_REPORT.md
```

The build environment returned HTTP 200 from the local server, but its Chromium policy blocked localhost and `file://` navigation with `ERR_BLOCKED_BY_ADMINISTRATOR`. For that reason this package does not misrepresent the attempted browser run as a pass; final responsive / visual inspection remains an explicit local pre-publish step.

## Local server

Direct server command:

```powershell
python -m http.server 8000
```

Open:

```text
http://localhost:8000/
```

A convenience validation + server script is also retained:

```powershell
.\scripts\run_public_experience.ps1
```

Do not open `index.html` directly with `file://`; use the local HTTP server so behavior matches deployment more closely.

## Release notes and source ledgers

- `FINAL_POLISH_RELEASE_NOTES.md`
- `assets/public/IMAGE_SOURCES.md`
- `assets/public/AUTHORITATIVE_SOURCE_AUDIT.md`
- `assets/public/FIGURE_AUDIT.md`

## Publishing

No deployment, merge-to-main, or push action is included in this package. Inspect the local site first.
