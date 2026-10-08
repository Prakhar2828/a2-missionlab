# A2 MissionLab Roadmap

## Phase 0 — Foundation

Goal: establish the mission data model, provenance rules, zero-cost architecture, source inventory, and a working static prototype.

Deliverables:

- project governance/disclaimer
- source catalog
- mission-event schema
- seed event timeline
- provenance UI
- decision-thread UI
- validator

## Phase 1 — Mission Backbone

Goal: create the authoritative temporal/geometric spine.

Work:

- ingest NASA AROW flight-derived ephemeris
- establish UTC and Mission Elapsed Time conversion
- compute Earth/Moon range and velocity quantities
- normalize major mission phases and maneuvers
- ingest PDS environmental sensor CSVs
- ingest the public lunar target request JSON
- validate event timestamps against primary NASA sources

Outcome: a mission clock that drives the whole application.

## Phase 2 — Flight Dynamics, GNC, Propulsion, Communications

Work:

- 3D Earth-Moon-Orion trajectory
- trajectory event markers
- lunar sphere-of-influence context
- maneuver timeline and cancellation decisions
- line-of-sight / lunar occultation geometry
- communications event reconstruction
- optical communications summary
- uncertainty and source labeling

## Phase 3 — ECLSS, Vehicle Systems, Thermal, Materials

Work:

- cabin/environmental trends from released sensors
- toilet fault and wastewater vent decision threads
- change-point/anomaly analysis labeled as project-derived
- Artemis I heat-shield root cause → Artemis II risk mitigation → postflight closure chain
- thermal protection / material science explainer backed by NASA technical sources

## Phase 4 — Entry, Descent, Splashdown, Recovery

Work:

- return geometry and entry timeline
- public entry events
- communications blackout
- modeled atmospheric quantities where raw telemetry is unavailable
- parachute sequence
- splashdown accuracy and recovery timeline
- explicit separation of public data and model outputs

## Phase 5 — Space Weather and Radiation

Work:

- ingest OMNI/CDAWeb-compatible public heliophysics quantities
- correlate space-weather context with mission clock
- prepare Artemis II trajectory input for NAIRAS 3.0
- ingest/export NAIRAS runs where permitted
- make assumptions such as shielding depth explicit
- distinguish external environment from astronaut dose

## Phase 6 — Lunar Science and Crew Observations

Work:

- index PDS crew imagery and Orion imagery metadata
- index mission audio/transcripts/annotations
- connect observation time, view direction, image, crew remark, and target
- integrate public LRO context products for selected targets
- reconstruct impact-flash observations, terminator observations, eclipse/corona observations, and Earth imagery analysis

## Phase 7 — Mission Control / Engineering Perspectives

Work:

- discipline lenses such as FLIGHT, FDO, FAO, EECOM, COMM, SCIENCE, engineering support
- shared timeline with discipline-specific prioritization
- decision threads: detection → evidence → constraint → options → decision → action → outcome
- postflight engineering timeline

## Phase 8 — Evidence-Grounded Mission Analyst

Work:

- structured retrieval over events/data/sources
- deterministic calculations exposed as tools
- citation-first answers
- optional local/browser LLM
- no paid model dependency

## Phase 9 — Publication Quality

Work:

- accessibility
- mobile/desktop behavior
- tests and CI
- methodology and validation reports
- performance optimization
- public deployment
- polished GitHub README and demo media
