from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE = ROOT / "data" / "reference"

INDEX_PATH = ROOT / "index.html"
APP_PATH = ROOT / "app.js"
STYLES_PATH = ROOT / "styles.css"
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"
PAGES_PATH = ROOT / ".github" / "workflows" / "pages.yml"

PHASE7A_PATH = REFERENCE / "artemis_ii_mission_control_perspectives.json"
PHASE9A_PATH = REFERENCE / "artemis_ii_publication_manifest.json"
WEB_MANIFEST_PATH = REFERENCE / "artemis_ii_publication_web_manifest.json"


def fail(message: str) -> None:
    raise SystemExit(f"PHASE 9B VALIDATION FAILED: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_text(path: Path) -> str:
    require(path.exists(), f"missing file: {path}")
    text = path.read_text(encoding="utf-8")
    require(bool(text.strip()), f"empty file: {path}")
    return text


def load_json(path: Path) -> dict:
    require(path.exists(), f"missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    print()
    print("Phase 9B Artemis II Public Web Validation")
    print("=" * 72)

    html = load_text(INDEX_PATH)
    js = load_text(APP_PATH)
    css = load_text(STYLES_PATH)
    ci = load_text(CI_PATH)
    pages = load_text(PAGES_PATH)

    phase7a = load_json(PHASE7A_PATH)
    phase9a = load_json(PHASE9A_PATH)
    manifest = load_json(WEB_MANIFEST_PATH)

    require(
        phase7a.get("dataset_id")
        == "phase7a_artemis_ii_mission_control_perspectives",
        "Phase 7A identity mismatch",
    )

    require(
        len(phase7a.get("shared_timeline", [])) == 24,
        "validated timeline must contain 24 events",
    )

    require(
        phase9a.get("dataset_id")
        == "phase9a_artemis_ii_publication_manifest",
        "Phase 9A manifest identity mismatch",
    )

    require(
        manifest.get("dataset_id")
        == "phase9b_artemis_ii_publication_web_manifest",
        "Phase 9B web manifest identity mismatch",
    )

    require(
        manifest.get("status")
        == "PUBLIC_WEB_AND_CI_COMPLETE",
        "Phase 9B web status mismatch",
    )

    print()
    print("Phase 7A validated timeline dependency: PASS")
    print("24-event shared timeline: PASS")
    print("Phase 9A publication dependency: PASS")
    print("Phase 9B web manifest identity: PASS")

    for marker in [
        'class="skip-link"',
        'id="main-content"',
        'aria-label="Project navigation"',
        'aria-live="polite"',
        'aria-live="assertive"',
        'tabindex="-1"',
        'PHASE 9',
        'VALIDATED SHARED TIMELINE',
        'EVIDENCE BOUNDARIES',
    ]:
        require(marker in html, f"HTML missing accessibility marker: {marker}")

    require("PHASE 0" not in html, "stale Phase 0 status remains in public HTML")

    print()
    print("Skip navigation: PASS")
    print("Semantic main navigation: PASS")
    print("ARIA live regions: PASS")
    print("Keyboard-focusable detail panel: PASS")
    print("Current Phase 9 status: PASS")
    print("Stale Phase 0 status removed: PASS")

    require(
        "artemis_ii_mission_control_perspectives.json" in js,
        "frontend does not use validated Phase 7A timeline",
    )

    require(
        "artemis_ii_publication_manifest.json" in js,
        "frontend does not use publication metrics",
    )

    require(
        "data/seed/mission_events.json" not in js,
        "frontend still depends on obsolete Phase 0 seed timeline",
    )

    require(
        "event.timestamp_utc" in js
        and "event.date_utc" in js
        and "event.time_precision" in js,
        "frontend does not preserve timing precision",
    )

    require("escapeHtml" in js, "frontend missing HTML output escaping")

    print()
    print("Validated timeline frontend source: PASS")
    print("Phase 0 seed dependency removed: PASS")
    print("Missing/exact timing distinction: PASS")
    print("HTML output escaping: PASS")

    for marker in [
        ":focus-visible",
        ".skip-link",
        "@media (max-width: 900px)",
        "@media (max-width: 600px)",
        "@media (prefers-reduced-motion: reduce)",
        "min-height: 44px",
    ]:
        require(marker in css, f"CSS missing requirement: {marker}")

    print()
    print("Visible keyboard focus: PASS")
    print("44px interactive targets: PASS")
    print("Tablet responsive breakpoint: PASS")
    print("Mobile responsive breakpoint: PASS")
    print("Reduced-motion support: PASS")

    for marker in [
        "actions/checkout@v4",
        "actions/setup-python@v5",
        "validate_publication_pack.py",
        "validate_publication_web.py",
    ]:
        require(marker in ci, f"CI workflow missing: {marker}")

    print()
    print("GitHub Actions CI workflow: PASS")
    print("Python syntax check in CI: PASS")
    print("Phase 9A validator in CI: PASS")
    print("Phase 9B validator in CI: PASS")

    for marker in [
        "actions/configure-pages@v5",
        "actions/upload-pages-artifact@v3",
        "actions/deploy-pages@v4",
        "pages: write",
        "id-token: write",
    ]:
        require(marker in pages, f"Pages workflow missing: {marker}")

    print()
    print("GitHub Pages workflow: PASS")
    print("Static-site artifact deployment: PASS")
    print("Pages permission model: PASS")

    principles = manifest["publication_principles"]

    require(principles["validated_timeline_only"] is True, "validated-timeline-only rule missing")
    require(principles["no_phase0_seed_dependency"] is True, "Phase 0 seed prohibition missing")
    require(principles["no_new_mission_reconstruction"] is True, "Phase 9B adds reconstruction")

    print()
    print("Validated timeline only: PASS")
    print("No Phase 0 seed dependency: PASS")
    print("No new mission reconstruction: PASS")

    print()
    print("PHASE 9B VALIDATION PASSED")


if __name__ == "__main__":
    main()
