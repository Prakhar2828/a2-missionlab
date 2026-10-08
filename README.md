# A2 MissionLab

**Artemis II Mission Operations & Engineering Reconstruction**

A2 MissionLab is an independent, open-source project that reconstructs NASA's Artemis II mission from public data and public technical sources. The long-term goal is to connect trajectory, mission operations, spacecraft systems, communications, space weather, lunar science, entry and recovery, engineering anomalies, and postflight findings through one synchronized mission clock.

> Independent project using publicly released NASA data. This is not an official NASA application and does not imply NASA endorsement.

## Current status

**Phase 0 — foundation scaffold**

The repository currently contains:

- a zero-cost architecture plan
- a public-data source catalog
- a provenance model
- a normalized mission-event schema
- a starter Artemis II event timeline
- a dependency-free web prototype that visualizes mission-critical events and decision threads
- a lightweight data validator

## Run locally

No package installation is required for the Phase 0 prototype.

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

## Design principles

1. **One mission clock.** Every subsystem view must resolve to a common UTC/MET timeline.
2. **Public evidence only.** No internal NASA material, unpublished telemetry, internal screenshots, internal URLs, or non-public procedures.
3. **Provenance everywhere.** Values are labeled as `FLIGHT_DATA`, `NASA_REPORTED`, `DERIVED`, `MODEL`, or `SYNTHETIC`.
4. **Physics before AI.** Deterministic code computes mission state; AI may retrieve and explain evidence but should not invent or numerically infer spacecraft state.
5. **No fake gauges.** If public telemetry does not exist, the UI explicitly says so.
6. **Reproducibility.** Every transformed dataset should have a source, transformation record, version, and validation path.

## Planned mission domains

- Mission overview / FLIGHT
- Flight dynamics / FDO
- GNC and spacecraft attitude
- Propulsion and maneuver history
- Communications and lunar occultation
- ECLSS and crew systems
- Space weather and radiation context
- Thermal protection and materials
- Entry, parachute descent, splashdown, recovery
- Lunar science and astronaut observations
- Human performance and biomedical objectives
- Ground / launch operations
- Anomalies, decisions, and decision threads
- Postflight engineering / MER-style analysis
- Evidence-grounded Mission Analyst

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the phased build plan.
