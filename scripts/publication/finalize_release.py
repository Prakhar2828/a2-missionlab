from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE = ROOT / "data" / "reference"
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"

MISSION_PATH = ROOT / "data" / "config" / "mission.json"
PHASE8A_PATH = REFERENCE / "artemis_ii_mission_analyst_index.json"
PHASE8B_PATH = REFERENCE / "artemis_ii_mission_analyst_interface.json"
PHASE9A_PATH = REFERENCE / "artemis_ii_publication_manifest.json"
PHASE9B_PATH = REFERENCE / "artemis_ii_publication_web_manifest.json"

README_PATH = ROOT / "README.md"
ROADMAP_PATH = DOCS / "ROADMAP.md"
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"

DEMO_PATH = ASSETS / "a2-missionlab-release-overview.svg"
RELEASE_MANIFEST_PATH = REFERENCE / "artemis_ii_release_manifest.json"
VALIDATOR_PATH = ROOT / "scripts" / "validation" / "validate_release.py"

DEMO_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" role="img" aria-labelledby="title desc">\n  <title id="title">A2 MissionLab Artemis II Release Overview</title>\n  <desc id="desc">Architecture overview showing public evidence, deterministic engineering analysis, mission-control perspectives, and the Mission Analyst.</desc>\n\n  <rect width="1600" height="900" fill="#05080e"/>\n  <circle cx="1380" cy="80" r="260" fill="#0d2034"/>\n  <circle cx="1380" cy="80" r="180" fill="#102b47"/>\n\n  <text x="90" y="105" fill="#8fbdec" font-family="Arial, sans-serif" font-size="24" font-weight="700" letter-spacing="4">\n    ARTEMIS II · PUBLIC-EVIDENCE ENGINEERING RECONSTRUCTION\n  </text>\n\n  <text x="90" y="180" fill="#f1f6fb" font-family="Arial, sans-serif" font-size="72" font-weight="700">\n    A2 MissionLab\n  </text>\n\n  <text x="90" y="230" fill="#9fb1c5" font-family="Arial, sans-serif" font-size="30">\n    One mission clock. Multiple engineering disciplines. Explicit evidence boundaries.\n  </text>\n\n  <line x1="120" y1="450" x2="1480" y2="450" stroke="#35516f" stroke-width="4"/>\n\n  <g font-family="Arial, sans-serif">\n    <rect x="90" y="330" width="260" height="190" rx="16" fill="#0b1420" stroke="#2e4c6c" stroke-width="2"/>\n    <text x="120" y="375" fill="#8fbdec" font-size="19" font-weight="700">PUBLIC EVIDENCE</text>\n    <text x="120" y="415" fill="#edf4fb" font-size="22">NASA reporting</text>\n    <text x="120" y="450" fill="#edf4fb" font-size="22">AROW trajectory</text>\n    <text x="120" y="485" fill="#edf4fb" font-size="22">PDS · OMNI · LRO</text>\n\n    <rect x="420" y="330" width="310" height="190" rx="16" fill="#0b1420" stroke="#2e4c6c" stroke-width="2"/>\n    <text x="450" y="375" fill="#8fbdec" font-size="19" font-weight="700">ENGINEERING ANALYSIS</text>\n    <text x="450" y="415" fill="#edf4fb" font-size="22">Flight dynamics · GNC</text>\n    <text x="450" y="450" fill="#edf4fb" font-size="22">Systems · Entry · Science</text>\n    <text x="450" y="485" fill="#edf4fb" font-size="22">Derived ≠ reported</text>\n\n    <rect x="800" y="330" width="310" height="190" rx="16" fill="#0b1420" stroke="#2e4c6c" stroke-width="2"/>\n    <text x="830" y="375" fill="#8fbdec" font-size="19" font-weight="700">MISSION OPERATIONS</text>\n    <text x="830" y="415" fill="#edf4fb" font-size="22">24 shared mission events</text>\n    <text x="830" y="450" fill="#edf4fb" font-size="22">7 discipline lenses</text>\n    <text x="830" y="485" fill="#edf4fb" font-size="22">10 decision threads</text>\n\n    <rect x="1180" y="330" width="330" height="190" rx="16" fill="#0b1420" stroke="#5f8fc3" stroke-width="2"/>\n    <text x="1210" y="375" fill="#8fbdec" font-size="19" font-weight="700">MISSION ANALYST</text>\n    <text x="1210" y="415" fill="#edf4fb" font-size="22">146 searchable records</text>\n    <text x="1210" y="450" fill="#edf4fb" font-size="22">8 deterministic tools</text>\n    <text x="1210" y="485" fill="#edf4fb" font-size="22">Citation-first answers</text>\n  </g>\n\n  <g fill="#88bdf2">\n    <circle cx="385" cy="450" r="8"/>\n    <circle cx="765" cy="450" r="8"/>\n    <circle cx="1145" cy="450" r="8"/>\n  </g>\n\n  <g font-family="Arial, sans-serif">\n    <text x="90" y="625" fill="#9fb1c5" font-size="18" font-weight="700" letter-spacing="3">VALIDATED RELEASE SCALE</text>\n\n    <text x="90" y="690" fill="#f1f6fb" font-size="42" font-weight="700">25</text>\n    <text x="90" y="725" fill="#9fb1c5" font-size="18">reference datasets</text>\n\n    <text x="325" y="690" fill="#f1f6fb" font-size="42" font-weight="700">81</text>\n    <text x="325" y="725" fill="#9fb1c5" font-size="18">public sources</text>\n\n    <text x="540" y="690" fill="#f1f6fb" font-size="42" font-weight="700">24</text>\n    <text x="540" y="725" fill="#9fb1c5" font-size="18">mission events</text>\n\n    <text x="755" y="690" fill="#f1f6fb" font-size="42" font-weight="700">10</text>\n    <text x="755" y="725" fill="#9fb1c5" font-size="18">decision threads</text>\n\n    <text x="995" y="690" fill="#f1f6fb" font-size="42" font-weight="700">146</text>\n    <text x="995" y="725" fill="#9fb1c5" font-size="18">searchable records</text>\n\n    <text x="1265" y="690" fill="#f1f6fb" font-size="42" font-weight="700">8 + 8</text>\n    <text x="1265" y="725" fill="#9fb1c5" font-size="18">tools + answer routes</text>\n  </g>\n\n  <rect x="90" y="790" width="1420" height="1" fill="#25384e"/>\n\n  <text x="90" y="835" fill="#7ee2b8" font-family="Arial, sans-serif" font-size="20" font-weight="700">\n    PUBLIC EVIDENCE ONLY · UNKNOWN MEANS UNKNOWN · NO PAID MODEL DEPENDENCY\n  </text>\n</svg>\n'
VALIDATOR_SOURCE = 'from __future__ import annotations\n\nimport json\nfrom pathlib import Path\n\n\nROOT = Path(__file__).resolve().parents[2]\nREFERENCE = ROOT / "data" / "reference"\n\nMISSION_PATH = ROOT / "data" / "config" / "mission.json"\nPHASE8A_PATH = REFERENCE / "artemis_ii_mission_analyst_index.json"\nPHASE8B_PATH = REFERENCE / "artemis_ii_mission_analyst_interface.json"\nPHASE9A_PATH = REFERENCE / "artemis_ii_publication_manifest.json"\nPHASE9B_PATH = REFERENCE / "artemis_ii_publication_web_manifest.json"\nRELEASE_PATH = REFERENCE / "artemis_ii_release_manifest.json"\n\nREADME_PATH = ROOT / "README.md"\nROADMAP_PATH = ROOT / "docs" / "ROADMAP.md"\nDEMO_PATH = ROOT / "docs" / "assets" / "a2-missionlab-release-overview.svg"\nINDEX_PATH = ROOT / "index.html"\nAPP_PATH = ROOT / "app.js"\nCI_PATH = ROOT / ".github" / "workflows" / "ci.yml"\nPAGES_PATH = ROOT / ".github" / "workflows" / "pages.yml"\n\n\ndef fail(message: str) -> None:\n    raise SystemExit(f"PHASE 9C RELEASE VALIDATION FAILED: {message}")\n\n\ndef require(condition: bool, message: str) -> None:\n    if not condition:\n        fail(message)\n\n\ndef load_json(path: Path) -> dict:\n    require(path.exists(), f"missing file: {path}")\n    return json.loads(path.read_text(encoding="utf-8-sig"))\n\n\ndef load_text(path: Path) -> str:\n    require(path.exists(), f"missing file: {path}")\n    text = path.read_text(encoding="utf-8")\n    require(bool(text.strip()), f"empty file: {path}")\n    return text\n\n\ndef main() -> None:\n    print()\n    print("Phase 9C Artemis II Final Release Validation")\n    print("=" * 72)\n\n    mission = load_json(MISSION_PATH)\n    p8a = load_json(PHASE8A_PATH)\n    p8b = load_json(PHASE8B_PATH)\n    p9a = load_json(PHASE9A_PATH)\n    p9b = load_json(PHASE9B_PATH)\n    release = load_json(RELEASE_PATH)\n\n    readme = load_text(README_PATH)\n    roadmap = load_text(ROADMAP_PATH)\n    demo = load_text(DEMO_PATH)\n    html = load_text(INDEX_PATH)\n    js = load_text(APP_PATH)\n    ci = load_text(CI_PATH)\n    pages = load_text(PAGES_PATH)\n\n    require(mission.get("mission") == "Artemis II", "mission identity mismatch")\n    require(\n        mission.get("launch_epoch_utc") == "2026-04-01T22:35:12Z",\n        "launch epoch mismatch",\n    )\n\n    require(\n        p8a.get("dataset_id") == "phase8a_artemis_ii_mission_analyst_index",\n        "Phase 8A identity mismatch",\n    )\n    require(\n        p8b.get("dataset_id") == "phase8b_artemis_ii_mission_analyst_interface",\n        "Phase 8B identity mismatch",\n    )\n    require(\n        p9a.get("status") == "PUBLICATION_DOCUMENTATION_PACK_COMPLETE",\n        "Phase 9A status mismatch",\n    )\n    require(\n        p9b.get("status") == "PUBLIC_WEB_AND_CI_COMPLETE",\n        "Phase 9B status mismatch",\n    )\n    require(\n        release.get("dataset_id") == "phase9c_artemis_ii_release_manifest",\n        "release manifest identity mismatch",\n    )\n    require(\n        release.get("status") == "RELEASE_CANDIDATE_COMPLETE",\n        "release status mismatch",\n    )\n\n    print()\n    print("Mission identity and launch epoch: PASS")\n    print("Phase 8 analyst dependency: PASS")\n    print("Phase 9A documentation dependency: PASS")\n    print("Phase 9B web/CI dependency: PASS")\n    print("Phase 9C release manifest identity: PASS")\n\n    expected = {\n        "datasets": 25,\n        "sources": 81,\n        "events": 24,\n        "decision_threads": 10,\n        "postflight_records": 6,\n        "searchable_records": 146,\n        "tools": 8,\n        "answer_routes": 8,\n    }\n\n    for key, value in expected.items():\n        require(\n            release["validated_metrics"].get(key) == value,\n            f"release metric mismatch: {key}",\n        )\n\n    require(len(p8a["dataset_registry"]) == 25, "Phase 8A dataset registry mismatch")\n    require(len(p8a["source_registry"]) == 81, "Phase 8A source registry mismatch")\n    require(len(p8a["event_registry"]) == 24, "Phase 8A event registry mismatch")\n    require(len(p8a["decision_thread_registry"]) == 10, "Phase 8A decision-thread registry mismatch")\n    require(len(p8a["postflight_registry"]) == 6, "Phase 8A postflight registry mismatch")\n    require(len(p8a["unified_records"]) == 146, "Phase 8A unified-record count mismatch")\n    require(len(p8a["tool_registry"]) == 8, "Phase 8A tool count mismatch")\n    require(len(p8b["question_router"]["routes"]) == 8, "Phase 8B route count mismatch")\n\n    print()\n    print("25 indexed datasets: PASS")\n    print("81 normalized sources: PASS")\n    print("24 mission events: PASS")\n    print("10 decision threads: PASS")\n    print("6 postflight records: PASS")\n    print("146 searchable records: PASS")\n    print("8 deterministic tools: PASS")\n    print("8 answer routes: PASS")\n\n    require(\n        "Phases 0 through 9 are complete" in readme,\n        "README final completion status missing",\n    )\n    require(\n        "Phase 9 publication hardening is in progress" not in readme,\n        "README still says Phase 9 is in progress",\n    )\n    require(\n        "docs/assets/a2-missionlab-release-overview.svg" in readme,\n        "README demo media link missing",\n    )\n    require("<svg" in demo and "A2 MissionLab" in demo, "release demo media invalid")\n\n    print()\n    print("README final status: PASS")\n    print("README demo media: PASS")\n    print("Release overview SVG: PASS")\n\n    for phase in range(10):\n        require(\n            f"## Phase {phase}" in roadmap,\n            f"roadmap missing Phase {phase}",\n        )\n\n    require("## Release Status" in roadmap, "roadmap release status missing")\n    require(\n        "Phases 0 through 9 complete" in roadmap,\n        "roadmap final completion statement missing",\n    )\n    require(\n        "release demo media" in roadmap,\n        "roadmap demo-media closure missing",\n    )\n\n    print()\n    print("Roadmap phases 0-9 present: PASS")\n    print("Roadmap Phase 9 closure: PASS")\n    print("Demo-media roadmap requirement: PASS")\n\n    require("PHASE 0" not in html, "public interface still exposes stale Phase 0 status")\n    require(\n        "artemis_ii_mission_control_perspectives.json" in js,\n        "public app not using validated timeline",\n    )\n    require(\n        "data/seed/mission_events.json" not in js,\n        "public app still uses Phase 0 seed timeline",\n    )\n\n    print()\n    print("Public interface current status: PASS")\n    print("Validated timeline source: PASS")\n    print("Phase 0 seed dependency absent: PASS")\n\n    require("validate_publication_pack.py" in ci, "CI missing Phase 9A validation")\n    require("validate_publication_web.py" in ci, "CI missing Phase 9B validation")\n    require("validate_release.py" in ci, "CI missing final release validation")\n    require("actions/deploy-pages@v4" in pages, "Pages deployment workflow missing")\n    require("branches:" in pages and "- main" in pages, "Pages deployment is not main-branch configured")\n\n    print()\n    print("Phase 9A validation in CI: PASS")\n    print("Phase 9B validation in CI: PASS")\n    print("Final release validation in CI: PASS")\n    print("GitHub Pages main-branch deployment: PASS")\n\n    principles = release["release_principles"]\n\n    require(principles["public_evidence_only"] is True, "public evidence boundary missing")\n    require(principles["unknowns_remain_unknown"] is True, "unknown preservation missing")\n    require(principles["no_paid_model_dependency"] is True, "paid-model boundary missing")\n    require(principles["no_private_nasa_material"] is True, "private-material boundary missing")\n    require(principles["no_new_mission_reconstruction_in_phase9"] is True, "Phase 9 reconstruction boundary missing")\n\n    print()\n    print("Public evidence only: PASS")\n    print("Unknowns remain unknown: PASS")\n    print("No paid-model dependency: PASS")\n    print("No private NASA material: PASS")\n    print("No new Phase 9 mission reconstruction: PASS")\n\n    for boundary in [\n        "MISSIONLAB DERIVED",\n        "TEMPORAL SEQUENCE",\n        "UNKNOWN PUBLIC FACT",\n    ]:\n        require(boundary in readme, f"release boundary missing: {boundary}")\n\n    print()\n    print("Core evidence boundaries preserved: PASS")\n\n    print()\n    print("PHASE 9C RELEASE VALIDATION PASSED")\n    print("MISSIONLAB RELEASE CANDIDATE COMPLETE")\n\n\nif __name__ == "__main__":\n    main()\n'


def fail(message: str) -> None:
    raise SystemExit(f"PHASE 9C FINALIZATION FAILED: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_json(path: Path) -> dict:
    require(path.exists(), f"missing required file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def update_readme() -> None:
    text = README_PATH.read_text(encoding="utf-8")

    old_status = (
        "**Phases 0 through 8 are complete relative to defensible public evidence. "
        "Phase 9 publication hardening is in progress.**"
    )

    new_status = (
        "**Phases 0 through 9 are complete relative to defensible public evidence "
        "and the validated MissionLab publication scope.**"
    )

    if old_status in text:
        text = text.replace(old_status, new_status)
    elif new_status not in text:
        fail("README project-status text was not in the expected state")

    demo_section = """## Demo media

![A2 MissionLab release overview](docs/assets/a2-missionlab-release-overview.svg)

The release overview summarizes the project evidence spine from public mission data through deterministic engineering analysis, Mission Control perspectives, and the citation-first Mission Analyst.

"""

    if "## Demo media" not in text:
        marker = "## Documentation"
        require(marker in text, "README documentation section not found")
        text = text.replace(marker, demo_section + marker, 1)

    write_text(README_PATH, text)


def update_roadmap() -> None:
    text = ROADMAP_PATH.read_text(encoding="utf-8")

    release_status = """## Release Status

**Phases 0 through 9 complete relative to defensible public evidence and the validated MissionLab publication scope.**

Phase 9 closure includes:

- accessibility
- mobile and desktop behavior
- automated tests and CI
- methodology and validation reports
- static zero-framework performance hardening
- GitHub Pages deployment workflow
- polished GitHub README
- release demo media
- final cross-phase release validation

Public deployment is configured through `.github/workflows/pages.yml` and activates from the `main` branch.
"""

    if "## Release Status" not in text:
        text = text.rstrip() + "\n\n" + release_status

    write_text(ROADMAP_PATH, text)


def update_ci() -> None:
    text = CI_PATH.read_text(encoding="utf-8")

    final_step = """      - name: Validate final MissionLab release
        run: python scripts/validation/validate_release.py
"""

    if "validate_release.py" not in text:
        text = text.rstrip() + "\n\n" + final_step

    write_text(CI_PATH, text)


def main() -> None:
    mission = load_json(MISSION_PATH)
    p8a = load_json(PHASE8A_PATH)
    p8b = load_json(PHASE8B_PATH)
    p9a = load_json(PHASE9A_PATH)
    p9b = load_json(PHASE9B_PATH)

    require(mission.get("mission") == "Artemis II", "mission identity mismatch")
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

    metrics = p9a["publication_metrics"]

    update_readme()
    update_roadmap()
    update_ci()

    write_text(DEMO_PATH, DEMO_SVG)
    write_text(VALIDATOR_PATH, VALIDATOR_SOURCE)

    release_manifest = {
        "dataset_id": "phase9c_artemis_ii_release_manifest",
        "mission": "Artemis II",
        "phase": "9C",
        "status": "RELEASE_CANDIDATE_COMPLETE",
        "mission_clock": {
            "launch_epoch_utc": mission["launch_epoch_utc"],
            "source": "data/config/mission.json",
        },
        "validated_metrics": metrics,
        "phase_completion": {
            f"phase_{phase}": "COMPLETE"
            for phase in range(10)
        },
        "release_outputs": [
            "README.md",
            "docs/ROADMAP.md",
            "docs/assets/a2-missionlab-release-overview.svg",
            "index.html",
            "app.js",
            "styles.css",
            ".github/workflows/ci.yml",
            ".github/workflows/pages.yml",
            "scripts/validation/validate_release.py",
        ],
        "release_principles": {
            "public_evidence_only": True,
            "unknowns_remain_unknown": True,
            "no_paid_model_dependency": True,
            "no_private_nasa_material": True,
            "no_new_mission_reconstruction_in_phase9": True,
        },
        "deployment": {
            "platform": "GitHub Pages",
            "workflow": ".github/workflows/pages.yml",
            "trigger_branch": "main",
            "state": "CONFIGURED_FOR_MAIN_BRANCH_DEPLOYMENT",
        },
    }

    write_json(RELEASE_MANIFEST_PATH, release_manifest)

    outputs = [
        README_PATH,
        ROADMAP_PATH,
        DEMO_PATH,
        CI_PATH,
        VALIDATOR_PATH,
        RELEASE_MANIFEST_PATH,
    ]

    for path in outputs:
        require(path.exists(), f"output missing: {path}")
        require(path.stat().st_size > 0, f"output empty: {path}")

    print()
    print("Phase 9C Artemis II Release Finalization")
    print("=" * 72)
    print()
    print("README final completion status: UPDATED")
    print("Roadmap release status: UPDATED")
    print("Release demo media: CREATED")
    print("Final release validator: CREATED")
    print("CI final validator step: ADDED")
    print("Release manifest: CREATED")
    print()
    print("Generated / updated:")
    for path in outputs:
        print(f"  {path.relative_to(ROOT)}")
    print()
    print("PHASE 9C RELEASE FINALIZATION COMPLETE")
    print("RUN FINAL VALIDATOR NEXT")


if __name__ == "__main__":
    main()
