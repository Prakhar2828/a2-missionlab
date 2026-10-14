# Phase I — Entry / Descent / Recovery QA Contract

## Product objective

Phase I upgrades the existing Mission-route Entry story without rebuilding it as a separate application. The public experience follows:

`lunar-return energy → atmospheric interaction → modeled heating / load → loft-rebound geometry → communications context → parachutes → splashdown → crew recovery → spacecraft recovery`

The public interaction lives at `mission.html#entry-lab`. Dedicated Phase I runtime and model code live in `js/entry.js` and `js/entry-model.js` so the shared Mission runtime does not require an uncontrolled rewrite.

## Two clocks, two evidence classes

The Phase I experience deliberately shows two kinds of time:

- **analysis time** — referenced to the first state in the 819-record high-rate flight-derived source at `2026-04-10T23:53:30.866Z`; analytical landmarks can have sub-second precision because they are derived from that source and MissionLab's validated processing chain.
- **NASA public event time** — Entry Interface, communications reacquisition, drogue deployment, main deployment, and splashdown are retained at the minute precision supported by NASA's public live updates.

A NASA-reported public minute is never promoted to an exact second-level telemetry epoch.

## High-rate reconstruction contract

The protected source identity remains:

- format: `PROP_MAN 11.0`
- frame label: `M50`
- position units: `FT`
- velocity units: `FPS`
- time units: `SEC`
- records: `819`
- source duration: `817.975 s`

The eighth raw numeric field remains unresolved. Phase I does not assign it a physical meaning.

The browser uses curated Phase 2 checkpoints to provide continuous visual interpolation. That interpolation is a visualization of the existing reconstruction, not a telemetry replay and not a reconstruction of Orion's private onboard navigation state.

## Aerothermal evidence boundary

The public heat-flux values use the existing low-fidelity Sutton–Graves stagnation-point convective-heating relation:

`q_dot = k * sqrt(rho / Rn) * V^3`

with the existing Phase 2 assumptions: modeled NRLMSIS 2.0 density, reconstructed Earth-relative speed, a `6.035 m` Orion EFT-1 heritage/reference nose radius, and a cold-wall engineering correlation.

Primary public interpretation remains limited to:

`Kn < 0.01 AND Mach >= 5`

Protected modeled peak:

- analysis `+85 s`
- altitude `61.878469 km`
- Earth-relative speed `9.984103 km/s`
- Mach `32.285653`
- modeled convective heat flux `109.641953 W/cm²`

The primary integrated modeled convective heat load remains `162.686370921 MJ/m²`; the stronger-continuum sensitivity remains `159.150073328 MJ/m²`.

These quantities are **MODELED external convective-heating estimates**. They are not measured Orion TPS telemetry, measured TPS temperature, char depth, ablation/recession, material damage, crew thermal exposure, or flight-qualified thermal analysis.

## Dynamic pressure versus heating teaching contract

Phase I protects a high-value relationship already established in Phase 2:

- early modeled dynamic-pressure peak: `12.798779 kPa` at analysis `+95 s`, with modeled heat flux `104.975953 W/cm²`
- later/global modeled dynamic-pressure peak: `12.808389 kPa` at analysis `+431 s`, with modeled heat flux `7.596440 W/cm²`

The pressure maxima differ by only about `0.075%`, while the modeled heating differs by more than an order of magnitude because dynamic pressure scales as `rho*V^2` and Sutton–Graves heating approximately as `sqrt(rho)*V^3`.

## Artemis II loft / rebound contract

The reconstructed vertical trajectory contains a real loft/rebound structure:

- start: analysis `+112.294128 s`, altitude `60.350128 km`, speed `8.993741 km/s`
- top/end: analysis `+239.647374 s`, altitude `64.211808 km`, speed `6.479165 km/s`
- duration: `127.353246 s`
- altitude recovery: `3.861680 km`
- speed loss: `2.514577 km/s`

Permanent terminology boundary:

`ARTEMIS II LOFT / REBOUND != ARTEMIS I SKIP ENTRY`

## Communications contract

NASA reported a planned plasma communications blackout shortly after Entry Interface, expected to last about six minutes, and public communications reacquisition at `00:00 UTC`.

Phase I must not invent exact blackout-start or blackout-end seconds. Expected entry blackout is operational context, not a communications anomaly, and the public blackout event is not a plasma-density measurement.

## Parachute and recovery contract

Protected NASA-reported Orion parachute architecture:

- 3 forward-bay-cover parachutes, approximately 7 ft each
- 2 drogues, approximately 23 ft each
- 3 pilots, approximately 11 ft each
- 3 mains, approximately 116 ft each

This is a system architecture reference, not an exact individual as-flown canopy performance log.

Protected public-minute recovery milestones include:

- recovery-team approach: `00:12 UTC`
- crew extracted: `01:34 UTC`
- crew aboard recovery ship: `01:58 UTC`
- Orion secured in the recovery ship well deck: `08:27 UTC`

The public-minute relationships remain:

- splashdown → crew aboard recovery ship: `111 min`
- splashdown → Orion secured in well deck: `500 min`

Crew recovery, spacecraft recovery, and postflight engineering closure remain different concepts.

## Splashdown boundary

MissionLab's derived WGS 84 surface crossing remains:

- `2026-04-11T00:07:08.823676Z`
- latitude `32.340599 deg`
- longitude `-117.763095 deg`

It lies within NASA's reported `00:07 UTC` splashdown minute. The `8.824 s` offset from the beginning of that public minute is a consistency diagnostic only, not an exact splashdown timing error.

No public official numerical target-coordinate + official actual-coordinate pair is established in the curated evidence. Therefore:

`OFFICIAL TARGET-TO-ACTUAL MISS DISTANCE = NOT PUBLICLY QUANTIFIABLE`

## Pure-model/evidence regression

`scripts/validation/validate_entry_model.js` must verify:

- high-rate source identity and unresolved-field boundary
- protected analysis checkpoints
- continuous interpolation remains finite
- heating peaks before the global dynamic-pressure peak
- the two dominant dynamic-pressure peaks remain nearly equal while modeled heating differs strongly
- loft/rebound altitude gain and speed loss remain intact
- public event anchors remain explicitly minute-resolution
- blackout exact timing is not synthesized
- modeled heating/dynamic pressure are not extrapolated beyond the protected Phase 2 hypersonic interpretation window
- splashdown/recovery non-equivalence boundaries remain intact

## Browser regression

`scripts/validation/entry_regression.html` and `scripts/validation/validate_entry_regression.py` must verify:

- continuous scrubber state at protected checkpoints
- loft/rebound behavior and non-skip terminology
- heating-versus-dynamic-pressure relationship
- planned-blackout versus anomaly boundary and public-minute reacquisition
- recovery closure milestones and splashdown boundary
- event-rail interaction
- canvas rendering
- finite public state
- no unintended horizontal overflow at phone portrait, larger phone portrait, phone landscape, and desktop viewports

On Windows release installation, Chrome and Edge are required.

## Protected regressions

Phase I must not regress:

- Mission Explorer
- Through Orion's Windows
- deterministic GNC AUTO / MANUAL behavior
- Mission Control
- PSI
- Trajectory Correction
- Space Weather
- global responsive browser QA

## Performance / architecture contract

Phase I retains the Phase 10 multi-page architecture. Entry stays on the Mission route, but its new model/runtime/style are isolated in dedicated files. The historical Entry block in `js/mission.js` is bypassed only when the Phase I root marker is present; unrelated Mission, Trajectory Correction, and Space Weather behavior remains untouched.

The only continuous animation loop is user-triggered playback. A paused Entry view redraws only on state or responsive geometry changes.
