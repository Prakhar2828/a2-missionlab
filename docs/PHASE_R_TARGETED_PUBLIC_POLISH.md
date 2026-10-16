# Phase R — Targeted Public Polish

## Scope

Phase R starts from production `main` at:

`ceb168770e78fbb8aab6bab2d5c1cbf74119df24`

and preserves the completed Phase P / Phase Q release architecture while making only the requested public-facing corrections.

## Critical Entry / Descent / Recovery rule

**The current Entry / Descent / Recovery simulation is not replaced.**

The production engineering experience remains intact and continues to load through the same files and controls:

- `js/entry.js`
- `js/entry-model.js`
- `entry.css`
- `#entry-flight-canvas`
- `#entry-scrubber`
- `#entry-play`
- current metric/readout, loft/rebound, blackout, parachute, recovery, and evidence-boundary surfaces

Phase R hard-checks the Git blob IDs for `js/entry.js`, `js/entry-model.js`, and `entry.css` against the production baseline before applying the patch, after applying it, after validation, and before commit. Any change to those files fails the installer.

The restored prior Entry visual is added separately through:

- `entry-visual.css`
- `js/entry-visual.js`
- `#entry-visual-companion`
- `#entry-visual-canvas`
- independent visual scrubber / play / reset controls

The two experiences intentionally coexist on the same Entry / Descent / Recovery section.

## Git-history recovery

### Space Weather

Useful prior implementation: commit `85bce6ae711cc60bebd714a0a02f9734626ef665` (`Redesign space weather lab`) records the replacement of the earlier Mission-route canvas. Its diff preserves the removed visualization concept: a Sun at the left, Earth / Orion context at the right, and animated particles advancing from the Sun toward the spacecraft context.

Recovered idea:

- clear Sun → disturbance → Earth / Orion spatial relationship
- motion moving away from the Sun toward the spacecraft context
- particle-field motion as a qualitative visual cue

Intentionally **not** restored:

- the former generic `solar activity 0–100` control
- the former conceptual shielding slider
- any mapping from visual travel time to physical SEP arrival time
- any visual implication that proton flux is crew absorbed dose

The recovered movement concept is rebuilt on top of the current Phase H physical proton-flux / NOAA S-scale model. Current inputs, outputs, evidence boundaries, and location semantics remain authoritative.

### Entry / Descent / Recovery

Useful prior implementation: commit `7adc22831845095dc35f40c88832f73a55319d20`, immediately before commit `31f37ee0c6ea27775d8621de29b6f0d31d618564` (`Upgrade entry descent and recovery`), contains the earlier visual sequence: Orion approaching the atmosphere, a heating trail, drogue and main parachutes, ocean, and splashdown progression.

Recovered idea:

- capsule visibly progresses from near-space / upper-atmosphere entry toward the ocean
- plasma / heating visualization during high-energy entry
- descent progression
- two-drogue and three-main parachute visual phases
- ocean / splashdown closure

Intentionally **not** restored:

- the earlier coarse milestone model as a replacement for Phase I
- old approximate readouts where the current Phase I reconstruction is more rigorous
- unsupported exact parachute seconds, attitude, landing coordinates, or private telemetry assumptions

Adaptation:

The restored sequence is an **additional visual companion** driven by the existing `A2EntryModel`. It owns separate DOM IDs and controls and does not write to the current engineering scrubber, engineering canvas, readouts, or play state. Browser QA snapshots the current engineering simulation, exercises the restored visual through parachute and splashdown phases, and confirms the current engineering state does not change.

## Other targeted changes

- Technical Report public baseline commit hash removed.
- Public cost language removed while preserving the GitHub Pages architecture description.
- Shared circular disclosure icon changed from font `+` / `−` glyphs to CSS-drawn centered strokes, avoiding browser/font baseline drift.
- PSI added as a first-class fifth option in the homepage “Choose your experience” grid using the existing PSI evidence boundary and model language.

## Validation contract

Phase R adds two targeted validators without weakening any existing gate:

- `python scripts/validation/validate_phase_r_targeted_polish.py`
- `python scripts/validation/validate_phase_r_targeted_regression.py --required`

The installer also runs:

- `git diff --check`
- Python compilation
- `node --check` for changed JavaScript plus the preserved current Entry runtime
- `python scripts/validation/validate_text_integrity.py`
- `python scripts/validate_public_experience.py`
- `python scripts/validation/validate_phase_p_release_candidate.py`
- `python scripts/validation/validate_phase_q_adversarial_review.py`
- `python scripts/validation/validate_creator_conversion.py`
- the existing Entry browser regression **before** the new visual regression
- targeted Space Weather browser regression
- global responsive browser QA
- Phase R targeted browser regression at 390×844, 430×932, 768×1024, 844×390, 1280×800, and 1440×900
- `python scripts/validation/validate_phase_p_regression.py --portable`
- on Windows, `python scripts/validation/validate_phase_p_regression.py --windows-release`

No test threshold, viewport, browser requirement, timeout policy, or evidence guardrail is weakened by Phase R.
