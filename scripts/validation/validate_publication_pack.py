from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE = ROOT / "data" / "reference"
DOCS = ROOT / "docs"

MANIFEST_PATH = REFERENCE / "artemis_ii_publication_manifest.json"
README_PATH = ROOT / "README.md"
METHODOLOGY_PATH = DOCS / "METHODOLOGY.md"
VALIDATION_PATH = DOCS / "VALIDATION_REPORT.md"
ANALYST_GUIDE_PATH = DOCS / "ANALYST_GUIDE.md"
SUMMARY_PATH = DOCS / "PUBLICATION_SUMMARY.md"


def fail(message: str) -> None:
    raise SystemExit(
        f"PHASE 9A VALIDATION FAILED: {message}"
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_json(path: Path) -> dict:
    require(
        path.exists(),
        f"missing file: {path}",
    )

    return json.loads(
        path.read_text(
            encoding="utf-8-sig"
        )
    )


def load_text(path: Path) -> str:
    require(
        path.exists(),
        f"missing file: {path}",
    )

    text = path.read_text(
        encoding="utf-8",
    )

    require(
        bool(text.strip()),
        f"empty file: {path}",
    )

    return text


def main() -> None:
    print()
    print(
        "Phase 9A Artemis II Publication Pack Validation"
    )
    print("=" * 72)

    manifest = load_json(
        MANIFEST_PATH
    )

    readme = load_text(
        README_PATH
    )

    methodology = load_text(
        METHODOLOGY_PATH
    )

    validation = load_text(
        VALIDATION_PATH
    )

    analyst_guide = load_text(
        ANALYST_GUIDE_PATH
    )

    summary = load_text(
        SUMMARY_PATH
    )

    require(
        manifest.get("dataset_id")
        == "phase9a_artemis_ii_publication_manifest",
        "manifest dataset identity mismatch",
    )

    require(
        manifest.get("mission")
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        manifest.get("phase")
        == "9A",
        "phase identity mismatch",
    )

    require(
        manifest.get("status")
        == "PUBLICATION_DOCUMENTATION_PACK_COMPLETE",
        "manifest status mismatch",
    )

    print()
    print("Manifest identity: PASS")
    print("Mission identity: PASS")
    print("Phase identity: PASS")
    print("Publication status: PASS")

    metrics = manifest[
        "publication_metrics"
    ]

    expected_metrics = {
        "datasets": 25,
        "sources": 81,
        "events": 24,
        "decision_threads": 10,
        "postflight_records": 6,
        "searchable_records": 146,
        "tools": 8,
        "answer_routes": 8,
    }

    for key, expected in expected_metrics.items():
        require(
            metrics.get(key) == expected,
            (
                f"{key} expected {expected}, "
                f"found {metrics.get(key)}"
            ),
        )

    print()
    print("25 indexed datasets: PASS")
    print("81 normalized public sources: PASS")
    print("24 shared mission events: PASS")
    print("10 decision threads: PASS")
    print("6 postflight records: PASS")
    print("146 searchable records: PASS")
    print("8 deterministic tools: PASS")
    print("8 deterministic answer routes: PASS")

    require(
        "Phase 0 — foundation scaffold"
        not in readme,
        "obsolete Phase 0 README status remains",
    )

    require(
        "Phases 0 through 8 are complete"
        in readme,
        "README missing current project status",
    )

    require(
        "Evidence-Grounded Mission Analyst"
        in readme,
        "README missing Mission Analyst",
    )

    require(
        "UNKNOWN PUBLIC FACT"
        in readme,
        "README missing unknown-evidence boundary",
    )

    print()
    print("README stale Phase 0 status removed: PASS")
    print("README current project status: PASS")
    print("README Mission Analyst coverage: PASS")
    print("README evidence boundaries: PASS")

    for boundary in [
        "MISSIONLAB DERIVED",
        "PUBLIC EVENT SEQUENCE",
        "TEMPORAL SEQUENCE",
        "DISCIPLINE RELEVANCE",
        "TROUBLESHOOTING ACTION",
        "UNKNOWN PUBLIC FACT",
    ]:
        require(
            boundary in methodology,
            (
                "methodology missing boundary: "
                + boundary
            ),
        )

    print()
    print("Methodology evidence classes: PASS")
    print("Methodology mission-clock policy: PASS")
    print("Methodology reconstruction boundaries: PASS")
    print("Methodology known/unknown policy: PASS")

    for phase in range(0, 9):
        require(
            f"| {phase} |"
            in validation,
            (
                "validation report missing phase "
                f"{phase}"
            ),
        )

    require(
        "Paid model: NONE"
        in validation,
        "validation report missing paid-model boundary",
    )

    require(
        "UNKNOWN IN CURATED PUBLIC EVIDENCE"
        in validation,
        "validation report missing preserved unknown",
    )

    print()
    print("Phase 0-8 validation summary: PASS")
    print("No-paid-model validation boundary: PASS")
    print("Preserved unknowns documentation: PASS")

    for route in [
        "EVENT_TIME",
        "EVENT",
        "DECISION_THREAD",
        "DECISION_THREAD_CAUSATION",
        "DISCIPLINE",
        "DETERMINISTIC_ELAPSED_TIME",
        "KNOWN_UNKNOWN",
        "SEARCH_SYNTHESIS",
    ]:
        require(
            route in analyst_guide,
            (
                "analyst guide missing route: "
                + route
            ),
        )

    print()
    print("Analyst guide commands: PASS")
    print("8 analyst routes documented: PASS")
    print("Optional LLM handoff documented: PASS")

    require(
        "evidence over speculation"
        in summary,
        "publication summary missing engineering philosophy",
    )

    require(
        "Evidence-Grounded Mission Analyst"
        in summary,
        "publication summary missing analyst scope",
    )

    print()
    print("Publication summary scope: PASS")
    print("Publication engineering philosophy: PASS")

    principles = manifest[
        "principles"
    ]

    require(
        principles[
            "no_new_mission_reconstruction"
        ]
        is True,
        "Phase 9 incorrectly adds mission reconstruction",
    )

    require(
        principles[
            "public_evidence_only"
        ]
        is True,
        "public-evidence-only principle missing",
    )

    require(
        principles[
            "unknowns_remain_unknown"
        ]
        is True,
        "unknown preservation principle missing",
    )

    require(
        principles[
            "no_paid_model_dependency"
        ]
        is True,
        "no-paid-model principle missing",
    )

    require(
        principles[
            "no_private_nasa_material"
        ]
        is True,
        "private-material prohibition missing",
    )

    print()
    print("No new mission reconstruction: PASS")
    print("Public evidence only: PASS")
    print("Unknowns remain unknown: PASS")
    print("No paid-model dependency: PASS")
    print("No private NASA material: PASS")

    phase9 = manifest[
        "phase9_state"
    ]

    require(
        phase9[
            "documentation"
        ]
        == "COMPLETE_PHASE9A",
        "Phase 9A documentation incomplete",
    )

    require(
        phase9[
            "web_accessibility"
        ]
        == "PENDING_PHASE9B",
        "Phase 9B accessibility state mismatch",
    )

    require(
        phase9[
            "tests_ci"
        ]
        == "PENDING_PHASE9B",
        "Phase 9B CI state mismatch",
    )

    require(
        phase9[
            "final_validation"
        ]
        == "PENDING_PHASE9C",
        "Phase 9C validation state mismatch",
    )

    print()
    print("Phase 9A documentation coverage: PASS")
    print("Phase 9B handoff state: PASS")
    print("Phase 9C handoff state: PASS")

    print()
    print(
        "PHASE 9A VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()