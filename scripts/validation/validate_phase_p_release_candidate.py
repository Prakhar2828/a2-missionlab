from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / ".github" / "workflows" / "ci.yml"
QA = ROOT / "docs" / "PHASE_P_RELEASE_CANDIDATE_QA.md"
PUBLIC_VALIDATOR = ROOT / "scripts" / "validate_public_experience.py"
ORCHESTRATOR = ROOT / "scripts" / "validation" / "validate_phase_p_regression.py"

PROTECTED_STATIC = [
    "scripts/validation/validate_text_integrity.py",
    "scripts/validate_public_experience.py",
    "scripts/validation/validate_publication_pack.py",
    "scripts/validation/validate_publication_web.py",
    "scripts/validation/validate_release.py",
    "scripts/validation/validate_phase_k_publication.py",
    "scripts/validation/validate_phase_l_typography.py",
    "scripts/validation/validate_phase_m_accessibility.py",
    "scripts/validation/validate_phase_n_performance.py",
    "scripts/validation/validate_phase_o_presentation.py",
]

PORTABLE_BROWSER = [
    "validate_mission_scroll_regression.py",
    "validate_windows_scroll_regression.py",
    "validate_gnc_auto_regression.py",
    "validate_mission_control_regression.py",
    "validate_psi_regression.py",
    "validate_trajectory_regression.py",
    "validate_space_weather_regression.py",
    "validate_entry_regression.py",
    "validate_responsive_browser_qa.py",
]

WINDOWS_EXHAUSTIVE = PORTABLE_BROWSER + [
    "validate_phase_k_regression.py",
    "validate_phase_l_regression.py",
    "validate_phase_m_regression.py",
    "validate_phase_n_regression.py",
    "validate_phase_o_regression.py",
]

MAJOR_ROUTES = [
    "index.html",
    "mission.html",
    "windows.html",
    "gnc.html",
    "mission-control.html",
    "psi.html",
    "library.html",
    "technical-report.html",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"PHASE P RELEASE-CANDIDATE VALIDATION FAILED: {message}")
    print("PASS:", message)


def main() -> int:
    print("A2 MissionLab Phase P release-candidate static validation")
    print("=" * 76)

    require(CI.is_file(), "CI workflow exists")
    require(QA.is_file(), "Phase P QA contract exists")
    require(ORCHESTRATOR.is_file(), "Phase P browser orchestrator exists")

    for route in MAJOR_ROUTES:
        require((ROOT / route).is_file(), f"major public route exists: {route}")

    for path in PROTECTED_STATIC:
        require((ROOT / path).is_file(), f"protected static/evidence validator exists: {path}")

    for script in WINDOWS_EXHAUSTIVE:
        require((ROOT / "scripts" / "validation" / script).is_file(), f"protected browser validator exists: {script}")

    ci = CI.read_text(encoding="utf-8")
    qa = QA.read_text(encoding="utf-8")
    public_validator = PUBLIC_VALIDATOR.read_text(encoding="utf-8")
    orchestrator = ORCHESTRATOR.read_text(encoding="utf-8")

    require("browser-actions/setup-chrome@v2" in ci, "portable CI installs Chrome runtime dependencies with the current action major")
    require("chrome-version: 155.0.8059.39" in ci, "portable CI pins the Chrome 155 runtime dependency generation")
    require("chrome-headless-shell-linux64.zip" in ci, "portable CI installs the automation-oriented Chrome Headless Shell")
    require('version="155.0.8059.39"' in ci, "portable CI pins the exact Chrome Headless Shell version")
    require("${version}/linux64/chrome-headless-shell-linux64.zip" in ci, "portable CI downloads the pinned Chrome Headless Shell artifact")
    require('echo "PHASE_P_CHROME=$binary" >> "$GITHUB_ENV"' in ci, "portable CI passes the pinned Headless Shell executable into Phase P")
    require('test -x "$binary"' in ci, "portable CI verifies the Headless Shell executable before qualification")
    require(
        "python scripts/validation/validate_phase_p_release_candidate.py" in ci,
        "portable CI runs the Phase P static release-candidate gate",
    )
    require(
        "python scripts/validation/validate_phase_p_regression.py --portable" in ci,
        "portable CI runs mandatory Phase P Chromium browser coverage",
    )
    require("continue-on-error: true" not in ci, "Phase P CI browser gate is not allowed to continue on error")

    for script in PORTABLE_BROWSER:
        require(script in orchestrator, f"portable Phase P orchestration includes {script}")
    for script in WINDOWS_EXHAUSTIVE:
        require(script in orchestrator, f"Windows Phase P orchestration includes {script}")

    require("--portable" in orchestrator, "Phase P orchestrator exposes portable mode")
    require("--windows-release" in orchestrator, "Phase P orchestrator exposes Windows release mode")
    require("--required" in orchestrator, "Phase P orchestration keeps protected browser requirements fail-closed")
    require("PHASE_P_CHROME" in orchestrator and "google-chrome" in orchestrator, "portable Phase P maps the setup action Chrome path into protected browser discovery")

    for portable_script in (
        "validate_mission_control_regression.py",
        "validate_responsive_browser_qa.py",
    ):
        portable_source = (
            ROOT
            / "scripts"
            / "validation"
            / portable_script
        ).read_text(encoding="utf-8")

        require(
            "shutil.which" in portable_source,
            f"{portable_script} supports PATH-based portable browser discovery",
        )
        require(
            'if os.name != "nt"' in portable_source,
            f"{portable_script} applies Linux Chromium no-sandbox launch compatibility",
        )
        require(
            'and os.name == "nt"' in portable_source,
            f"{portable_script} reserves dual Edge+Chrome requirement for Windows",
        )
        require(
            "for name in sorted(browsers)" in portable_source,
            f"{portable_script} executes every discovered portable Chromium-family browser",
        )

    responsive_harness = (
        ROOT
        / "scripts"
        / "validation"
        / "responsive_browser_qa.html"
    ).read_text(encoding="utf-8")

    require(
        "&trajectory-qa=1" in responsive_harness,
        "responsive QA enables static Mission Explorer animation mode",
    )

    for phrase in [
        "iPhone Safari on physical hardware",
        "Android Chrome on physical hardware",
        "physical tablet browser testing",
        "desktop Safari where accessible",
        "NOT AUTOMATED BY PHASE P",
        "Phase Q owns the adversarial executive review/final polish",
    ]:
        require(phrase in qa, f"manual/device QA boundary documented: {phrase}")

    require("Phase P" in public_validator, "public release validator requires Phase P artifacts")
    require("validate_phase_p_release_candidate.py" in public_validator, "public release validator requires Phase P static gate")
    require("validate_phase_p_regression.py" in public_validator, "public release validator requires Phase P browser orchestrator")
    require("PHASE_P_RELEASE_CANDIDATE_QA.md" in public_validator, "public release validator requires Phase P QA document")

    require("PHASE Q COMPLETE" not in qa.upper(), "Phase P QA does not falsely claim Phase Q completion")

    print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
