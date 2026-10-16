# Phase R7 — Cinematic additive Entry visual upgrade

## Scope

Phase R7 upgrades only the supplemental Entry / Descent / Recovery visual companion. The current Phase I engineering simulation remains the protected primary reconstruction and is not modified.

Protected unchanged files:

- `js/entry.js`
- `js/entry-model.js`
- `entry.css`

R7 upgrades:

- `js/entry-visual.js`
- `entry-visual.css`

R7 validation additions:

- `scripts/validation/validate_phase_r7_cinematic_entry.py`
- `scripts/validation/phase_r7_cinematic_entry_regression.html`
- `scripts/validation/validate_phase_r7_cinematic_entry_regression.py`

## Visual design intent

The visual companion now behaves as a sequence of distinct camera contexts rather than a single schematic Earth-arc view:

1. Near-space view with Earth curvature and atmospheric limb.
2. Atmospheric-entry view with heating/plasma emphasis and fading stars.
3. Atmospheric descent with sky, haze, cloud bands, and ocean horizon.
4. Drogue recovery view.
5. Main-parachute descent view.
6. Ocean-only splashdown/recovery view with water interaction and a floating capsule.

The ocean recovery scene deliberately contains no Earth-outline / globe framing.

## Evidence boundary

The scene remains an educational, model-driven companion. Camera framing, capsule orientation, visual plasma, cloud layers, parachute motion, and water response are illustrative. They are not presented as an official NASA camera view, private telemetry, exact vehicle attitude, exact deployment dynamics, crew dose, or an as-flown photoreal reconstruction.

Public-minute parachute/splashdown anchors and the existing `A2EntryModel` continue to define the timing/state boundaries. The current engineering simulation remains authoritative for the page's evidence-aware quantitative interpretation.
