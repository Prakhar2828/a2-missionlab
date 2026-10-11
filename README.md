# A2 MissionLab

**Evidence-Grounded Artemis II Mission Operations & Engineering Reconstruction**

A2 MissionLab is an independent open-source engineering project that reconstructs NASA's Artemis II mission from publicly released mission data, NASA technical sources, planetary-data products, public mission reporting, and deterministic analysis.

> A2 MissionLab is not an official NASA application, is not NASA-endorsed, and does not use non-public NASA data, internal procedures, internal screenshots, or unpublished telemetry.

## Project status

**Phases 0 through 8 are complete relative to defensible public evidence. Phase 9 publication hardening is in progress.**

| Capability | Count |
|---|---:|
| Indexed reference datasets | 25 |
| Normalized public sources | 81 |
| Shared mission events | 24 |
| Decision threads | 10 |
| Postflight engineering records | 6 |
| Unified searchable analyst records | 146 |
| Deterministic analyst tools | 8 |
| Deterministic answer routes | 8 |

## Mission domains

A2 MissionLab covers:

- mission clock and trajectory backbone
- Earth-Moon geometry and lunar flyby
- maneuver chronology
- GNC and navigation architecture
- Orion propulsion
- communications and blackout reconstruction
- spacecraft-system anomalies
- thermal protection
- entry, descent, splashdown, and recovery
- space weather and radiation interfaces
- lunar science and crew observations
- Mission Control perspectives
- engineering decision threads
- postflight engineering
- Evidence-Grounded Mission Analyst

## Provenance model

MissionLab distinguishes:

- `FLIGHT_DATA`
- `NASA_REPORTED`
- `DERIVED`
- `MODEL`
- `SYNTHETIC`

Critical rules include:

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
TROUBLESHOOTING ACTION
!=
CONFIRMED ROOT CAUSE
```

```text
EXPECTED COMMUNICATIONS CONSTRAINT
!=
COMMUNICATIONS ANOMALY
```

```text
UNKNOWN PUBLIC FACT
!=
PERMISSION TO INVENT
```

See [docs/METHODOLOGY.md](docs/METHODOLOGY.md) and [docs/PROVENANCE.md](docs/PROVENANCE.md).

## Evidence-Grounded Mission Analyst

The analyst supports deterministic:

- event lookup
- decision-thread lookup
- source lookup
- dataset lookup
- keyword search
- UTC to MET
- MET to UTC
- elapsed-time calculations
- citation-first answers
- known / unknown handling
- discipline-aware answers
- causation guardrails

No paid model or API key is required.

### Example questions

```text
When was RTC2?

Did the return-link loss cause RTC2?

What was the root cause of the urine vent-line issue?

How long was it between Earthset and Earthrise?

What does the SCIENCE perspective focus on?

What happened with the Artemis II heat shield?

What happened at Entry Interface?
```

## Quick start

Create a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the web application:

```powershell
python -m http.server 8000
```

Open:

```text
http://localhost:8000
```

Build the Mission Analyst index:

```powershell
.\.venv\Scripts\python.exe scripts\analyst\mission_analyst.py build-index
```

Build the citation-first interface:

```powershell
.\.venv\Scripts\python.exe scripts\analyst\answer_mission_question.py build-interface
```

Ask a mission question:

```powershell
.\.venv\Scripts\python.exe scripts\analyst\answer_mission_question.py ask "Did the return link loss cause RTC2?"
```

## Documentation

- [Methodology](docs/METHODOLOGY.md)
- [Validation Report](docs/VALIDATION_REPORT.md)
- [Mission Analyst Guide](docs/ANALYST_GUIDE.md)
- [Publication Summary](docs/PUBLICATION_SUMMARY.md)
- [Provenance Standard](docs/PROVENANCE.md)
- [Engineering Log](docs/ENGINEERING_LOG.md)
- [Roadmap](docs/ROADMAP.md)
- [Disclaimer](DISCLAIMER.md)

## Design principles

1. One mission clock.
2. Public evidence only.
3. Provenance everywhere.
4. Physics before AI.
5. No fake telemetry.
6. Unknown means unknown.
7. Reproducible calculations and validation.
8. Zero-cost core architecture.

## License

MIT. See [LICENSE](LICENSE).
