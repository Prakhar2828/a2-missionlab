# A2 MissionLab Methodology

## Purpose

A2 MissionLab reconstructs Artemis II mission operations and engineering context from defensible public evidence.

The project does not attempt to reconstruct private NASA console records, unpublished telemetry, or undisclosed flight-controller reasoning.

## Core workflow

1. Establish one common mission clock.
2. Preserve public source products.
3. Calculate only quantities supported by explicit inputs.
4. Separate observation from interpretation.
5. Independently validate major reconstruction boundaries.

## Evidence classes

### FLIGHT_DATA

Direct publicly released flight-derived data.

### NASA_REPORTED

Facts or events publicly reported by NASA.

### DERIVED

Deterministic MissionLab calculations from public inputs.

Examples include:

- Mission Elapsed Time
- Moon-relative geometry
- sphere-of-influence transitions
- elapsed event times

Derived values are not relabeled as NASA telemetry.

### MODEL

Physical or statistical estimates with explicit assumptions.

### SYNTHETIC

Invented test or training data only.

Synthetic content is never treated as mission evidence.

## Mission clock

Artemis II launch epoch:

```text
2026-04-01T22:35:12Z
```

All mission domains use the same UTC / Mission Elapsed Time reference.

Approximate public times remain approximate.

Missing exact times are not fabricated.

## Flight dynamics

Public flight-derived ephemeris products form the geometric mission backbone.

MissionLab may derive:

- Earth-centered range
- Moon-relative geometry
- lunar sphere-of-influence transitions
- pericynthion
- event-to-trajectory correlation

```text
PUBLIC AROW STATE
!=
ONBOARD NAVIGATION STATE
```

## Maneuvers

MissionLab distinguishes:

```text
PLANNED
CANCELLED
EXECUTED
```

A cancelled maneuver is not a failed burn.

## Communications

MissionLab separates:

```text
EXPECTED GEOMETRY CONSTRAINT
PLANNED ENTRY BLACKOUT
UNEXPECTED COMMUNICATIONS ANOMALY
```

```text
TEMPORAL SEQUENCE
!=
CAUSATION
```

## GNC and navigation

MissionLab reconstructs public architecture and capabilities.

It does not infer private:

- guidance laws
- controller gains
- unpublished onboard state histories
- unreported navigation residuals

## Spacecraft systems

Troubleshooting evidence does not automatically establish a root cause.

```text
POSSIBLE ICE
!=
CONFIRMED ICE
```

Open public investigations remain open.

## Thermal protection

MissionLab separates:

- Artemis I heat-shield behavior
- public root-cause findings
- Artemis II mitigation
- Artemis II entry implementation
- Artemis II postflight outcome

Modeled heating is not TPS telemetry.

## Space weather and radiation

External heliophysics context is not equivalent to astronaut dose.

```text
EXTERNAL ENVIRONMENT
!=
ASTRONAUT DOSE
```

## Lunar science

MissionLab connects:

- imagery
- mission audio
- annotations
- mission geometry
- lunar targets
- LRO context
- postflight interpretation

Observation opportunity is not automatically confirmed observation.

## Mission Control perspectives

Analytical lenses include:

```text
FLIGHT
FDO
FAO
EECOM
COMM
SCIENCE
ENGINEERING_SUPPORT
```

Decision threads use:

```text
detection
→ evidence
→ constraint
→ options
→ decision
→ action
→ outcome
```

Discipline relevance does not imply private decision authority.

## Mission Analyst

The Mission Analyst operates on validated structured MissionLab evidence.

Retrieval is deterministic.

Calculations are deterministic.

Every factual claim requires citations.

Unknown information may correctly return:

```text
UNKNOWN IN CURATED PUBLIC EVIDENCE
```

Optional LLM handoff is presentation-only and does not replace the evidence layer.

## Critical boundaries

```text
MISSIONLAB DERIVED
!=
NASA REPORTED
```

```text
PUBLIC EVENT SEQUENCE
!=
COMPLETE PRIVATE FLIGHT LOOP
```

```text
TEMPORAL SEQUENCE
!=
CAUSATION
```

```text
DISCIPLINE RELEVANCE
!=
DECISION AUTHORITY
```

```text
TROUBLESHOOTING ACTION
!=
CONFIRMED ROOT CAUSE
```

```text
EXPECTED CONSTRAINT
!=
ANOMALY
```

```text
UNKNOWN PUBLIC FACT
!=
PERMISSION TO INVENT
```

## Reproducibility

Major analysis code lives under:

```text
scripts/analysis/
scripts/processing/
scripts/analyst/
```

Independent validators live under:

```text
scripts/validation/
```

Tracked evidence products live primarily under:

```text
data/reference/
```
