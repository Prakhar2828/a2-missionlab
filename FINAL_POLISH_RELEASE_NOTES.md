# A2 MissionLab — Final Public Experience Polish

Release date: 2026-10-12
Working branch target: `public-experience-v3`
Overlay target: repository root

This overlay is the final UX / interaction polish layer for the existing validated A2 MissionLab public experience. It intentionally leaves validated Phase 0–9 engineering data, analysis pipelines, and source datasets outside the overlay.


## Final publish-readiness fixes — 2026-10-13
- Removed the Mission Control entry-scenario text collision by moving the canvas reacquisition label to the upper-right and making the event overlay effectively opaque.
- Separated the **Through Orion’s Windows** provenance label from the `01 / 25` counter on desktop and mobile layouts.
- Increased site-wide typography readability by scaling all explicitly small rem text declarations while preserving the existing hierarchy. The smallest explicit rem size is now `0.74rem`; body/inherited copy also receives a modest readability bump.
- Increased small canvas annotations throughout the interactive simulations.
- No content model, evidence boundary, gallery ordering, mission logic, or major layout architecture was changed in this patch.

## What changed

### Through Orion's Windows
- Expanded the experience to **25 Artemis II mission moments** sourced from NASA mission imagery.
- Added visible previous / next controls directly on the main image, a persistent image counter, keyboard left/right navigation, the existing lower timeline, scrubber, and filmstrip navigation.
- Removed the two distracting interior window-frame bars while retaining the subtle outer Orion-window framing.
- Added richer lunar-science, crew-observation, Earthset / Earthrise, eclipse, far-side, Mission Control science, and return-flight moments.
- Preserved explicit provenance boundaries for exact-event, near-event, same-phase, ground-context, and MissionLab-derived contextualization.

### Fly Orion / GNC
- Added **AUTO MODE** and **MANUAL MODE**.
- AUTO demonstrates a simplified closed guidance loop that senses error, estimates state, guides, controls, fires conceptual RCS, verifies the result, and converges on the target corridor.
- MANUAL exposes the existing THC / RHC teaching controls for the visitor.
- Restored **Introduce disturbance** in both modes. AUTO recovers; MANUAL makes the visitor recover.
- Added a loop-state readout and clearer control-purpose messaging.
- Rebuilt the GNC loop styling and the two public GNC / navigation SVG diagrams to remove awkward arrows and text overflow.

### Mission Control
- Added a beginner-facing role guide explaining FLIGHT, FDO, FAO, EECOM, SCIENCE, COMM, and ENG SUPPORT.
- Expanded role labels so users see both the shorthand and the meaning / function.
- Explicitly labels COMM and ENG SUPPORT as MissionLab educational lenses rather than claiming exact Artemis II front-room console nomenclature.
- Strengthened scenario decision traces and role-focused questions.

### Trajectory Correction Lab
- Added an operational HUD for coast time, conceptual arrival shift, and mission effect.
- Added stronger animated divergence feedback and a burn pulse so small corrections feel consequential without implying a high-fidelity trajectory simulation.
- Preserved the existing plan-versus-execution and cancellation-as-valid-decision framing.

### Space Weather Operations
- Reworked the three outputs into plain-language severity / posture readouts.
- Added inline definitions explaining crew-radiation concern, electronics environment, and operations posture.
- Added a dynamic "what operators would care about" action card.
- Preserved the explicit boundary that this is qualitative teaching context, not Artemis II crew dosimetry.

### PSI
- Split the ambiguous plume control into separate **engine cant angle** and **plume spread half-angle** controls.
- Added inline help, tooltips, definition cards, and nearby-hardware exposure feedback.
- The canvas now visually separates plume centerline direction (cant) from cone width (spread).
- Preserved the explicit boundary that Artemis II did not land on the Moon and that PSI is future-Artemis conceptual context.

## Evidence and source updates
- `assets/public/IMAGE_SOURCES.md` now inventories all 25 gallery moments and their provenance.
- `assets/public/AUTHORITATIVE_SOURCE_AUDIT.md` now includes the gallery provenance boundary, preliminary impact-flash science context, Mission Control role sourcing, and the MissionLab shorthand boundary.
- Current Artemis campaign framing remains aligned with NASA's 2026 architecture: Artemis III is a 2027 low-Earth-orbit demonstration and Artemis IV targets the first Artemis lunar landing in early 2028.

## Validation performed in this build environment
- `node --check app.js` — PASS
- `python -m py_compile scripts/validate_public_experience.py` — PASS
- XML parse of updated GNC SVGs — PASS
- CSS parse with `tinycss2` — PASS, zero top-level parse errors
- duplicate HTML IDs — PASS, none found
- required interaction IDs / final-polish semantics — PASS
- `python scripts/validate_public_experience.py --overlay-only` — PASS
- local HTTP server response — PASS (`HTTP 200`)

A live Chromium interaction run was attempted, but this execution environment blocks browser navigation to localhost and local file URLs with `ERR_BLOCKED_BY_ADMINISTRATOR`. The release therefore does **not** claim a successful live browser run in this environment. The packaged validation report records the limitation and the static/behavioral checks that were completed instead. Final visual inspection should be done from the local HTTP server after extraction.

## Scope
No merge, deployment, branch-publish, or push command is included. Inspect the local site first.
