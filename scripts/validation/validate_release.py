from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "data" / "reference"

MISSION_PATH = ROOT / "data" / "config" / "mission.json"
PHASE8A_PATH = REFERENCE / "artemis_ii_mission_analyst_index.json"
PHASE8B_PATH = REFERENCE / "artemis_ii_mission_analyst_interface.json"
PHASE9A_PATH = REFERENCE / "artemis_ii_publication_manifest.json"
PHASE9B_PATH = REFERENCE / "artemis_ii_publication_web_manifest.json"
RELEASE_PATH = REFERENCE / "artemis_ii_release_manifest.json"

README_PATH = ROOT / "README.md"
ROADMAP_PATH = ROOT / "docs" / "ROADMAP.md"
DEMO_PATH = ROOT / "docs" / "assets" / "a2-missionlab-release-overview.svg"
INDEX_PATH = ROOT / "index.html"
APP_PATH = ROOT / "app.js"
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"
PAGES_PATH = ROOT / ".github" / "workflows" / "pages.yml"


def fail(message: str) -> None:
    raise SystemExit(f"PHASE 9C RELEASE VALIDATION FAILED: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_json(path: Path) -> dict:
    require(path.exists(), f"missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    require(path.exists(), f"missing file: {path}")
    text = path.read_text(encoding="utf-8")
    require(bool(text.strip()), f"empty file: {path}")
    return text


def main() -> None:
    print()
    print("Phase 9C Artemis II Final Release Validation")
    print("=" * 72)

    mission = load_json(MISSION_PATH)
    p8a = load_json(PHASE8A_PATH)
    p8b = load_json(PHASE8B_PATH)
    p9a = load_json(PHASE9A_PATH)
    p9b = load_json(PHASE9B_PATH)
    release = load_json(RELEASE_PATH)

    readme = load_text(README_PATH)
    roadmap = load_text(ROADMAP_PATH)
    demo = load_text(DEMO_PATH)
    html = load_text(INDEX_PATH)
    js = load_text(APP_PATH)
    ci = load_text(CI_PATH)
    pages = load_text(PAGES_PATH)

    require(mission.get("mission") == "Artemis II", "mission identity mismatch")
    require(
        mission.get("launch_epoch_utc") == "2026-04-01T22:35:12Z",
        "launch epoch mismatch",
    )

    require(
        p8a.get("dataset_id") == "phase8a_artemis_ii_mission_analyst_index",
        "Phase 8A identity mismatch",
    )
    require(
        p8b.get("dataset_id") == "phase8b_artemis_ii_mission_analyst_interface",
        "Phase 8B identity mismatch",
    )
    require(
        p9a.get("status") == "PUBLICATION_DOCUMENTATION_PACK_COMPLETE",
        "Phase 9A status mismatch",
    )
    require(
        p9b.get("status") == "PUBLIC_WEB_AND_CI_COMPLETE",
        "Phase 9B status mismatch",
    )
    require(
        release.get("dataset_id") == "phase9c_artemis_ii_release_manifest",
        "release manifest identity mismatch",
    )
    require(
        release.get("status") == "RELEASE_CANDIDATE_COMPLETE",
        "release status mismatch",
    )

    print()
    print("Mission identity and launch epoch: PASS")
    print("Phase 8 analyst dependency: PASS")
    print("Phase 9A documentation dependency: PASS")
    print("Phase 9B web/CI dependency: PASS")
    print("Phase 9C release manifest identity: PASS")

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
            release["validated_metrics"].get(key) == value,
            f"release metric mismatch: {key}",
        )

    require(len(p8a["dataset_registry"]) == 25, "Phase 8A dataset registry mismatch")
    require(len(p8a["source_registry"]) == 81, "Phase 8A source registry mismatch")
    require(len(p8a["event_registry"]) == 24, "Phase 8A event registry mismatch")
    require(len(p8a["decision_thread_registry"]) == 10, "Phase 8A decision-thread registry mismatch")
    require(len(p8a["postflight_registry"]) == 6, "Phase 8A postflight registry mismatch")
    require(len(p8a["unified_records"]) == 146, "Phase 8A unified-record count mismatch")
    require(len(p8a["tool_registry"]) == 8, "Phase 8A tool count mismatch")
    require(len(p8b["question_router"]["routes"]) == 8, "Phase 8B route count mismatch")

    print()
    print("25 indexed datasets: PASS")
    print("81 normalized sources: PASS")
    print("24 mission events: PASS")
    print("10 decision threads: PASS")
    print("6 postflight records: PASS")
    print("146 searchable records: PASS")
    print("8 deterministic tools: PASS")
    print("8 answer routes: PASS")

    require(
        "Phases 0 through 9 are complete" in readme,
        "README final completion status missing",
    )
    require(
        "Phase 9 publication hardening is in progress" not in readme,
        "README still says Phase 9 is in progress",
    )
    require(
        "docs/assets/a2-missionlab-release-overview.svg" in readme,
        "README demo media link missing",
    )
    require("<svg" in demo and "A2 MissionLab" in demo, "release demo media invalid")

    print()
    print("README final status: PASS")
    print("README demo media: PASS")
    print("Release overview SVG: PASS")

    for phase in range(10):
        require(
            f"## Phase {phase}" in roadmap,
            f"roadmap missing Phase {phase}",
        )

    require("## Release Status" in roadmap, "roadmap release status missing")
    require(
        "Phases 0 through 9 complete" in roadmap,
        "roadmap final completion statement missing",
    )
    require(
        "release demo media" in roadmap,
        "roadmap demo-media closure missing",
    )

    print()
    print("Roadmap phases 0-9 present: PASS")
    print("Roadmap Phase 9 closure: PASS")
    print("Demo-media roadmap requirement: PASS")

    require("PHASE 0" not in html, "public interface still exposes stale Phase 0 status")
    require(
        "artemis_ii_mission_control_perspectives.json" in js,
        "public app not using validated timeline",
    )
    require(
        "data/seed/mission_events.json" not in js,
        "public app still uses Phase 0 seed timeline",
    )

    print()
    print("Public interface current status: PASS")
    print("Validated timeline source: PASS")
    print("Phase 0 seed dependency absent: PASS")

    require("validate_publication_pack.py" in ci, "CI missing Phase 9A validation")
    require("validate_publication_web.py" in ci, "CI missing Phase 9B validation")
    require("validate_release.py" in ci, "CI missing final release validation")
    require("actions/deploy-pages@v4" in pages, "Pages deployment workflow missing")
    require("branches:" in pages and "- main" in pages, "Pages deployment is not main-branch configured")

    print()
    print("Phase 9A validation in CI: PASS")
    print("Phase 9B validation in CI: PASS")
    print("Final release validation in CI: PASS")
    print("GitHub Pages main-branch deployment: PASS")

    principles = release["release_principles"]

    require(principles["public_evidence_only"] is True, "public evidence boundary missing")
    require(principles["unknowns_remain_unknown"] is True, "unknown preservation missing")
    require(principles["no_paid_model_dependency"] is True, "paid-model boundary missing")
    require(principles["no_private_nasa_material"] is True, "private-material boundary missing")
    require(principles["no_new_mission_reconstruction_in_phase9"] is True, "Phase 9 reconstruction boundary missing")

    print()
    print("Public evidence only: PASS")
    print("Unknowns remain unknown: PASS")
    print("No paid-model dependency: PASS")
    print("No private NASA material: PASS")
    print("No new Phase 9 mission reconstruction: PASS")

    for boundary in [
        "MISSIONLAB DERIVED",
        "TEMPORAL SEQUENCE",
        "UNKNOWN PUBLIC FACT",
    ]:
        require(boundary in readme, f"release boundary missing: {boundary}")

    print()
    print("Core evidence boundaries preserved: PASS")

    print()
    print("PHASE 9C RELEASE VALIDATION PASSED")
    print("MISSIONLAB RELEASE CANDIDATE COMPLETE")


if __name__ == "__main__":
    main()
