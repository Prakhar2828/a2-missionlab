from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE = ROOT / "data" / "reference"
DOCS = ROOT / "docs"

MISSION_PATH = ROOT / "data" / "config" / "mission.json"

PHASE8A_PATH = REFERENCE / "artemis_ii_mission_analyst_index.json"
PHASE8B_PATH = REFERENCE / "artemis_ii_mission_analyst_interface.json"

README_PATH = ROOT / "README.md"
METHODOLOGY_PATH = DOCS / "METHODOLOGY.md"
VALIDATION_PATH = DOCS / "VALIDATION_REPORT.md"
ANALYST_GUIDE_PATH = DOCS / "ANALYST_GUIDE.md"
PUBLICATION_SUMMARY_PATH = DOCS / "PUBLICATION_SUMMARY.md"

MANIFEST_PATH = REFERENCE / "artemis_ii_publication_manifest.json"


def fail(message: str) -> None:
    raise SystemExit(
        f"PHASE 9A PUBLICATION BUILD FAILED: {message}"
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_json(path: Path) -> dict:
    require(
        path.exists(),
        f"missing required file: {path}",
    )

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8-sig"
            )
        )
    except json.JSONDecodeError as exc:
        fail(
            f"invalid JSON in {path}: {exc}"
        )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        text.rstrip() + "\n",
        encoding="utf-8",
    )


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    mission = load_json(
        MISSION_PATH
    )

    phase8a = load_json(
        PHASE8A_PATH
    )

    phase8b = load_json(
        PHASE8B_PATH
    )

    require(
        mission.get("mission") == "Artemis II",
        "mission.json mission identity mismatch",
    )

    require(
        mission.get("launch_epoch_utc")
        == "2026-04-01T22:35:12Z",
        "launch epoch mismatch",
    )

    require(
        phase8a.get("dataset_id")
        == "phase8a_artemis_ii_mission_analyst_index",
        "Phase 8A dataset mismatch",
    )

    require(
        phase8b.get("dataset_id")
        == "phase8b_artemis_ii_mission_analyst_interface",
        "Phase 8B dataset mismatch",
    )

    metrics = {
        "datasets": len(
            phase8a["dataset_registry"]
        ),
        "sources": len(
            phase8a["source_registry"]
        ),
        "events": len(
            phase8a["event_registry"]
        ),
        "decision_threads": len(
            phase8a["decision_thread_registry"]
        ),
        "postflight_records": len(
            phase8a["postflight_registry"]
        ),
        "searchable_records": len(
            phase8a["unified_records"]
        ),
        "tools": len(
            phase8a["tool_registry"]
        ),
        "answer_routes": len(
            phase8b["question_router"]["routes"]
        ),
    }

    expected = {
        "datasets": 25,
        "sources": 81,
        "events": 24,
        "decision_threads": 10,
        "postflight_records": 6,
        "searchable_records": 146,
        "tools": 8,
        "answer_routes": 8,
    }

    for key, value in expected.items():
        require(
            metrics[key] == value,
            (
                f"{key} expected {value}, "
                f"found {metrics[key]}"
            ),
        )

    readme = f"""# A2 MissionLab

**Evidence-Grounded Artemis II Mission Operations & Engineering Reconstruction**

A2 MissionLab is an independent open-source engineering project that reconstructs NASA's Artemis II mission from publicly released mission data, NASA technical sources, planetary-data products, public mission reporting, and deterministic analysis.

> A2 MissionLab is not an official NASA application, is not NASA-endorsed, and does not use non-public NASA data, internal procedures, internal screenshots, or unpublished telemetry.

## Project status

**Phases 0 through 8 are complete relative to defensible public evidence. Phase 9 publication hardening is in progress.**

| Capability | Count |
|---|---:|
| Indexed reference datasets | {metrics["datasets"]} |
| Normalized public sources | {metrics["sources"]} |
| Shared mission events | {metrics["events"]} |
| Decision threads | {metrics["decision_threads"]} |
| Postflight engineering records | {metrics["postflight_records"]} |
| Unified searchable analyst records | {metrics["searchable_records"]} |
| Deterministic analyst tools | {metrics["tools"]} |
| Deterministic answer routes | {metrics["answer_routes"]} |

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
.\\.venv\\Scripts\\Activate.ps1
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
.\\.venv\\Scripts\\python.exe scripts\\analyst\\mission_analyst.py build-index
```

Build the citation-first interface:

```powershell
.\\.venv\\Scripts\\python.exe scripts\\analyst\\answer_mission_question.py build-interface
```

Ask a mission question:

```powershell
.\\.venv\\Scripts\\python.exe scripts\\analyst\\answer_mission_question.py ask "Did the return link loss cause RTC2?"
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
"""

    methodology = """# A2 MissionLab Methodology

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
"""

    validation = f"""# A2 MissionLab Validation Report

## Validation standard

A2 MissionLab independently validates major reconstruction stages for chronology, source identity, provenance, deterministic calculations, and evidence boundaries.

Completion means complete relative to defensible public evidence.

## Validated inventory

| Item | Count |
|---|---:|
| Indexed reference datasets | {metrics["datasets"]} |
| Normalized public sources | {metrics["sources"]} |
| Shared mission events | {metrics["events"]} |
| Decision threads | {metrics["decision_threads"]} |
| Postflight records | {metrics["postflight_records"]} |
| Unified analyst records | {metrics["searchable_records"]} |
| Deterministic analyst tools | {metrics["tools"]} |
| Deterministic answer routes | {metrics["answer_routes"]} |

## Phase status

| Phase | Domain | Status |
|---|---|---|
| 0 | Foundation | Complete |
| 1 | Mission backbone | Complete |
| 2 | Flight dynamics / GNC / propulsion / communications | Complete |
| 3 | Vehicle systems / thermal protection | Complete |
| 4 | Entry / descent / recovery | Complete |
| 5 | Space weather / radiation | Complete |
| 6 | Lunar science | Complete |
| 7 | Mission Control perspectives | Complete |
| 8 | Evidence-Grounded Mission Analyst | Complete |
| 9 | Publication quality | In progress |

## Major validation boundaries

```text
PUBLIC OEM
!=
ONBOARD NAVIGATION STATE
```

```text
CANCELLED BURN
!=
FAILED BURN
```

```text
EXPECTED BLACKOUT
!=
COMMUNICATIONS ANOMALY
```

```text
TROUBLESHOOTING ACTION
!=
CONFIRMED ROOT CAUSE
```

```text
MISSIONLAB GEOMETRY
!=
ONBOARD TELEMETRY
```

```text
TEMPORAL SEQUENCE
!=
CAUSATION
```

```text
UNKNOWN PUBLIC FACT
!=
PERMISSION TO INVENT
```

## Phase 8 validation

Validated:

```text
{metrics["datasets"]} datasets
{metrics["sources"]} public sources
{metrics["events"]} events
{metrics["decision_threads"]} decision threads
{metrics["postflight_records"]} postflight records
{metrics["searchable_records"]} searchable records
{metrics["tools"]} deterministic tools
{metrics["answer_routes"]} deterministic answer routes
```

Core analyst operation requires:

```text
Paid model: NONE
API key: NONE
Embedded model execution: NONE
```

## Preserved unknowns

```text
urine vent-line final root cause
UNKNOWN IN CURATED PUBLIC EVIDENCE
```

```text
private Mission Control dialogue
NOT RECONSTRUCTED
```

```text
exact onboard navigation state
NOT INFERRED FROM PUBLIC AROW DATA
```

A more detailed unsupported answer is not considered more correct than an explicit unknown.
"""

    analyst_guide = """# A2 MissionLab Analyst Guide

## Build the index

```powershell
.\\.venv\\Scripts\\python.exe scripts\\analyst\\mission_analyst.py build-index
```

## Build the answer interface

```powershell
.\\.venv\\Scripts\\python.exe scripts\\analyst\\answer_mission_question.py build-interface
```

## Show statistics

```powershell
.\\.venv\\Scripts\\python.exe scripts\\analyst\\mission_analyst.py stats
```

## Event lookup

```powershell
.\\.venv\\Scripts\\python.exe scripts\\analyst\\mission_analyst.py event A2_RTC2
```

## Decision-thread lookup

```powershell
.\\.venv\\Scripts\\python.exe scripts\\analyst\\mission_analyst.py thread RETURN_LINK_ANOMALY_RTC2
```

## Search

```powershell
.\\.venv\\Scripts\\python.exe scripts\\analyst\\mission_analyst.py search "return link RTC2"
```

## UTC to MET

```powershell
.\\.venv\\Scripts\\python.exe scripts\\analyst\\mission_analyst.py tool utc-to-met 2026-04-10T02:53:00Z
```

## Ask a mission question

```powershell
.\\.venv\\Scripts\\python.exe scripts\\analyst\\answer_mission_question.py ask "When was RTC2?"
```

## Supported routes

```text
EVENT_TIME
EVENT
DECISION_THREAD
DECISION_THREAD_CAUSATION
DISCIPLINE
DETERMINISTIC_ELAPSED_TIME
KNOWN_UNKNOWN
SEARCH_SYNTHESIS
```

## Known / unknown behavior

A valid response may be:

```text
UNKNOWN_IN_CURATED_PUBLIC_EVIDENCE
```

The analyst does not invent missing information.

## Optional local LLM handoff

```powershell
.\\.venv\\Scripts\\python.exe scripts\\analyst\\answer_mission_question.py handoff "What happened with the Artemis II heat shield?" --target local
```

## Optional browser LLM handoff

```powershell
.\\.venv\\Scripts\\python.exe scripts\\analyst\\answer_mission_question.py handoff "What happened with the Artemis II heat shield?" --target browser
```

Neither handoff executes a model.

## Authority hierarchy

```text
validated evidence
↓
deterministic retrieval
↓
deterministic calculations
↓
citation-first claims
↓
optional presentation model
```
"""

    publication_summary = f"""# A2 MissionLab Publication Summary

A2 MissionLab is an evidence-grounded public reconstruction of Artemis II mission operations and engineering.

## Validated scale

```text
{metrics["datasets"]} indexed reference datasets
{metrics["sources"]} normalized public sources
{metrics["events"]} shared mission events
{metrics["decision_threads"]} decision threads
{metrics["postflight_records"]} postflight engineering records
{metrics["searchable_records"]} searchable analyst records
{metrics["tools"]} deterministic analyst tools
{metrics["answer_routes"]} deterministic answer routes
```

## Technical scope

- trajectory ingestion
- SPICE lunar geometry
- maneuver reconstruction
- GNC
- navigation
- propulsion
- communications
- spacecraft systems
- thermal protection
- entry and recovery
- atmospheric and heating models
- space weather
- radiation interfaces
- lunar science
- Mission Control perspectives
- decision threads
- postflight engineering
- Evidence-Grounded Mission Analyst

## Engineering philosophy

```text
evidence over speculation

physics over fake telemetry

known unknowns over invented answers

deterministic calculation over opaque inference

provenance over presentation
```

## Disclaimer

A2 MissionLab is an independent open-source project.

It is not an official NASA application and does not imply NASA endorsement.
"""

    manifest = {
        "dataset_id": (
            "phase9a_artemis_ii_publication_manifest"
        ),
        "mission": "Artemis II",
        "phase": "9A",
        "status": (
            "PUBLICATION_DOCUMENTATION_PACK_COMPLETE"
        ),
        "mission_clock": {
            "launch_epoch_utc": (
                mission["launch_epoch_utc"]
            ),
            "source": (
                "data/config/mission.json"
            ),
        },
        "publication_metrics": metrics,
        "generated_documents": [
            "README.md",
            "docs/METHODOLOGY.md",
            "docs/VALIDATION_REPORT.md",
            "docs/ANALYST_GUIDE.md",
            "docs/PUBLICATION_SUMMARY.md",
        ],
        "principles": {
            "no_new_mission_reconstruction": True,
            "public_evidence_only": True,
            "unknowns_remain_unknown": True,
            "no_paid_model_dependency": True,
            "no_private_nasa_material": True,
        },
        "phase9_state": {
            "documentation": "COMPLETE_PHASE9A",
            "readme": "COMPLETE_PHASE9A",
            "methodology": "COMPLETE_PHASE9A",
            "validation_summary": "COMPLETE_PHASE9A",
            "analyst_guide": "COMPLETE_PHASE9A",
            "web_accessibility": "PENDING_PHASE9B",
            "mobile_desktop_behavior": "PENDING_PHASE9B",
            "tests_ci": "PENDING_PHASE9B",
            "performance_optimization": "PENDING_PHASE9B",
            "deployment_readiness": "PENDING_PHASE9B",
            "final_validation": "PENDING_PHASE9C",
        },
    }

    write_text(
        README_PATH,
        readme,
    )

    write_text(
        METHODOLOGY_PATH,
        methodology,
    )

    write_text(
        VALIDATION_PATH,
        validation,
    )

    write_text(
        ANALYST_GUIDE_PATH,
        analyst_guide,
    )

    write_text(
        PUBLICATION_SUMMARY_PATH,
        publication_summary,
    )

    write_json(
        MANIFEST_PATH,
        manifest,
    )

    generated = [
        README_PATH,
        METHODOLOGY_PATH,
        VALIDATION_PATH,
        ANALYST_GUIDE_PATH,
        PUBLICATION_SUMMARY_PATH,
        MANIFEST_PATH,
    ]

    for path in generated:
        require(
            path.exists(),
            f"output missing: {path}",
        )

        require(
            path.stat().st_size > 0,
            f"output empty: {path}",
        )

    print()
    print(
        "Phase 9A Artemis II Publication Documentation Pack"
    )
    print(
        "=" * 72
    )

    print()
    print(
        "Publication metrics:"
    )
    print(
        f"  reference datasets: {metrics['datasets']}"
    )
    print(
        f"  public sources: {metrics['sources']}"
    )
    print(
        f"  mission events: {metrics['events']}"
    )
    print(
        f"  decision threads: {metrics['decision_threads']}"
    )
    print(
        f"  postflight records: {metrics['postflight_records']}"
    )
    print(
        f"  searchable records: {metrics['searchable_records']}"
    )
    print(
        f"  analyst tools: {metrics['tools']}"
    )
    print(
        f"  answer routes: {metrics['answer_routes']}"
    )

    print()
    print(
        "Generated:"
    )

    for path in generated:
        print(
            f"  {path.relative_to(ROOT)}"
        )

    print()
    print(
        "PHASE 9A PUBLICATION DOCUMENTATION PACK COMPLETE"
    )


if __name__ == "__main__":
    main()
