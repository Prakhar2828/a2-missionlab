# Phase H — Space Weather Redesign QA

## Product objective

Teach the defensible chain:

`space phenomenon → measurement → physical consequence → mission/crew implication`

without converting an external environmental indicator into crew dose.

## Primary interaction

The previous generic `solar activity 0–100` and `conceptual shielding 0–100` controls were removed.

The Phase H scenario control is integral proton flux at energies `>=10 MeV`, reported in `pfu` (`particles / (cm^2 s sr)`) on a logarithmic axis. Public presets map to NOAA Solar Radiation Storm reference thresholds:

- below S1: 1 pfu teaching baseline
- S1: 10 pfu
- S2: 100 pfu
- S3: 1,000 pfu
- S4: 10,000 pfu
- S5: 100,000 pfu

This is a public severity reference, not an Artemis II flight rule.

## Mission context

Phase 5A NASA OMNI context remains separate from the SEP scenario. The public UI exposes four validated mission-window extrema:

- solar-wind speed max: 789.7 km/s at 2026-04-03 15:52 UTC
- Bz GSM min: -14.46 nT at 2026-04-02 07:09 UTC
- flow-pressure max: 11.75 nPa at 2026-04-10 07:16 UTC
- SYM/H min: -104 nT at 2026-04-02 08:41 UTC

OMNI is near-Earth bow-shock context. It is not Orion-local radiation and is not crew dose.

## NAIRAS version resolution

Repository history remains intact:

- Phase 5B prepared a NAIRAS 3.0 trajectory interface.
- 3,262 public-trajectory rows were prepared.
- no MissionLab NAIRAS run was submitted.
- no run ID or run output was ingested.
- no Orion-specific shielding depth was assumed.
- no NAIRAS-derived Artemis II dose was reported.

Current NASA CCMC documentation is NAIRAS Version 4. Its public changelog records Version 4.15 released for production on 2026-06-08. Phase H uses current Version 4 documentation for present-day model description while preserving the older Version 3.0 interface as historical repository analysis.

## Artemis II monitoring context

Public NASA material describes six HERA active radiation sensors inside Orion and crew-worn active dosimeters. MissionLab uses that fact to explain why radiation is operationally measurable, but does not claim access to private/as-flown crew dose values or NASA internal action thresholds.

## Protected evidence boundaries

- OMNI context != Orion-local radiation field
- >=10 MeV proton flux != absorbed dose
- proton flux != crew effective dose
- NOAA S-scale != Artemis II flight rule
- mission location != shielding model
- historical NAIRAS 3.0 interface != NAIRAS Version 4 run
- model output != dosimeter measurement
- no public shielding depth -> no invented Orion shielding input

## Validation requirements

Phase H adds:

- pure-model regression for pfu conversion and S1-S5 thresholds
- evidence-manifest cross-checks
- browser regression for baseline state, all six presets, location invariance, crew-dose boundary, current-vs-historical NAIRAS distinction, canvas render, and phone overflow
- existing public/text validation
- all protected browser regressions
- global responsive Chrome/Edge release gate in the Windows installer

The runtime is intentionally event-driven rather than a perpetual animation loop, reducing interference with protected Mission-route browser QA. Mission/Entry continuous canvases are reduced to a single frame only when `trajectory-qa=1` or `space-weather-qa=1` is present; normal production behavior is unchanged.
