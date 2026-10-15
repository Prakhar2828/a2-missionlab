from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "docs" / "PHASE_Q_ADVERSARIAL_REVIEW.md"
README = ROOT / "README.md"
VALIDATION_REPORT = ROOT / "docs" / "VALIDATION_REPORT.md"
PUBLIC_COMPAT = ROOT / "PUBLIC_EXPERIENCE_FINAL_README.md"
RELEASE_NOTES = ROOT / "FINAL_POLISH_RELEASE_NOTES.md"
PATCH_MANIFEST = ROOT / "PATCH_MANIFEST.txt"
IMAGE_LEDGER = ROOT / "assets" / "public" / "IMAGE_SOURCES.md"
FIGURE_AUDIT = ROOT / "assets" / "public" / "FIGURE_AUDIT.md"
CI = ROOT / ".github" / "workflows" / "ci.yml"
PUBLIC_VALIDATOR = ROOT / "scripts" / "validate_public_experience.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"PHASE Q ADVERSARIAL REVIEW VALIDATION FAILED: {message}")
    print("PASS:", message)


def read(path: Path) -> str:
    require(path.is_file(), f"required Phase Q artifact exists: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    print("A2 MissionLab Phase Q adversarial review / final polish validation")
    print("=" * 78)

    review = read(REVIEW)
    readme = read(README)
    validation = read(VALIDATION_REPORT)
    public_compat = read(PUBLIC_COMPAT)
    release_notes = read(RELEASE_NOTES)
    patch_manifest = read(PATCH_MANIFEST)
    image_ledger = read(IMAGE_LEDGER)
    figure_audit = read(FIGURE_AUDIT)
    ci = read(CI)
    public_validator = read(PUBLIC_VALIDATOR)

    reviewer_headings = [
        "SpaceX technical leadership",
        "NASA leadership",
        "Blue Origin leadership",
        "Flight director / flight operations",
        "GNC engineer",
        "EDL engineer",
        "Principal software engineer",
        "Recruiter",
    ]
    for reviewer in reviewer_headings:
        require(re.search(rf"^## Adversarial review \d+ — {re.escape(reviewer)}$", review, re.M) is not None,
                f"separate adversarial review recorded: {reviewer}")

    for phrase in [
        "Route quality scorecard",
        "Component-level review",
        "Final definition-of-done review",
        "Remaining hard limitations",
        "physical iPhone Safari",
        "physical Android Chrome",
        "real assistive-technology/screen-reader review",
        "No public route HTML",
        "large runtime files",
        "No below-9 route-level score is hidden",
    ]:
        require(phrase in review, f"Phase Q review preserves required boundary: {phrase}")

    route_rows = [
        "| Home |",
        "| Mission Explorer |",
        "| Through Orion's Windows |",
        "| GNC |",
        "| Mission Control |",
        "| PSI |",
        "| Mission Library |",
        "| Technical Report |",
    ]
    for row in route_rows:
        require(row in review, f"Phase Q route score recorded: {row.strip('| ')}")

    averages = [float(value) for value in re.findall(r"\|\s*(9\.\d)\s*\|\s*$", review, re.M)]
    require(len(averages) >= 8, "Phase Q scorecard contains route averages")
    require(all(value >= 9.0 for value in averages[:8]), "every major route average is at least 9.0")

    require("Phase P" in readme and "Phase Q" in readme, "README reports Phase P qualification and Phase Q closure")
    require("Phases 0 through 9 are complete" in readme, "README preserves historical publication-completion contract")
    require("| 9 | Publication quality | Complete |" in validation,
            "validation report no longer marks Phase 9 in progress")
    require("In progress" not in validation, "validation report contains no stale in-progress release status")

    stale_surfaces = "\n".join([public_compat, release_notes, patch_manifest, image_ledger, figure_audit])
    for stale in [
        "public-experience-v3",
        "validation/public-experience-final-polish/BROWSER_VALIDATION_REPORT.md",
        "validation/public-experience-final-polish/browser-validation.json",
        "SHA256SUMS.txt",
        "No validated repository artifact is deleted by this overlay",
    ]:
        require(stale not in stale_surfaces, f"stale overlay-era reference removed: {stale}")

    require("The overlay does not bundle NASA photography" not in image_ledger,
            "image source ledger describes the integrated repository, not an overlay")
    require("Earth ? NASA" not in image_ledger and "Moon ? NASA" not in image_ledger,
            "image source ledger has no legacy encoding placeholder in celestial headings")

    require("python scripts/validation/validate_phase_q_adversarial_review.py" in ci,
            "CI runs the Phase Q static review/polish gate")
    require("validate_phase_q_adversarial_review.py" in public_validator,
            "public release validation requires the Phase Q contract")
    require("PHASE_Q_ADVERSARIAL_REVIEW.md" in public_validator,
            "public release validation requires the Phase Q review record")

    require("PHASE Q COMPLETE" not in review.upper(),
            "review document does not bypass deterministic installer closure")

    print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
