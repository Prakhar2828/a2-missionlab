# Provenance Standard

Every meaningful value shown by A2 MissionLab should carry a provenance class.

| Class | Meaning | Example |
|---|---|---|
| `FLIGHT_DATA` | Direct value from a public flight-derived or mission dataset | Orion state vector from the released Artemis II ephemeris |
| `NASA_REPORTED` | Fact/event published by NASA but not available as raw telemetry in the project | NASA-reported communications loss |
| `DERIVED` | Deterministic quantity calculated from public source data | Earth range calculated from state vectors |
| `MODEL` | Estimate from a physical/statistical model with assumptions | Modeled heating or NAIRAS radiation quantity |
| `SYNTHETIC` | Explicitly invented scenario for testing or education | Training-only failure injection |

## Required provenance fields

Each normalized record should include, when applicable:

- `provenance_class`
- `source_agency`
- `source_title`
- `source_url`
- `source_product_id`
- `retrieved_at`
- `processing_version`
- `assumptions`
- `limitations`

## UI behavior

The provenance label must be visible without opening developer tools. A user should be able to distinguish NASA-released data from a value calculated by A2 MissionLab immediately.
