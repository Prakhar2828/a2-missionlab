from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ENTRY_BLOBS = {
    "js/entry.js": "6d14588227e56f7d41422301233a17d00ac2ffde",
    "js/entry-model.js": "169c860861d1b34f47f4a6349b8000e012ef12bb",
    "entry.css": "6d29af4e09af1beadca2d613a0c7c3319755c375",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"PHASE R TARGETED POLISH VALIDATION FAILED: {message}")
    print("PASS:", message)


def read(path: str) -> str:
    target = ROOT / path
    require(target.is_file(), f"required file exists: {path}")
    return target.read_text(encoding="utf-8")


def git_blob(path: str) -> str:
    completed = subprocess.run(
        ["git", "hash-object", "--", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    require(completed.returncode == 0, f"git can hash current Entry file: {path}")
    return completed.stdout.strip()


def main() -> int:
    print("A2 MissionLab Phase R targeted public-polish static validation")
    print("=" * 78)

    report = read("technical-report.html")
    index = read("index.html")
    mission = read("mission.html")
    styles = read("styles.css")
    landing = read("landing.css")
    weather = read("js/space-weather.js")
    entry_visual = read("js/entry-visual.js")
    entry_visual_css = read("entry-visual.css")

    require("Study baseline" not in report, "public Technical Report no longer exposes Study baseline")
    require("c7758aa415928467da0ebb6e48c276c1082be566" not in report, "public Technical Report no longer exposes baseline hash")
    require("Static GitHub Pages deployment" in report, "delivery architecture retained without cost language")

    public_files = [
        "index.html", "mission.html", "windows.html", "gnc.html", "mission-control.html", "psi.html",
        "library.html", "technical-report.html", "styles.css", "landing.css", "windows.css", "gnc.css",
        "mission-control.css", "psi.css", "trajectory.css", "entry.css", "entry-visual.css", "space-weather.css", "app.js",
        "js/core.js", "js/mission.js", "js/windows.js", "js/gnc.js", "js/mission-control.js", "js/psi.js",
        "js/trajectory.js", "js/entry.js", "js/entry-visual.js", "js/space-weather.js",
    ]
    public_text = "\n".join((ROOT / p).read_text(encoding="utf-8") for p in public_files if (ROOT / p).is_file())
    finance_patterns = [
        r"\$\s*0\b", r"\bzero[- ]cost\b", r"\bno[- ]cost\b", r"\bongoing\s+cost\b",
        r"\bcost[- ]efficient\b", r"\bzero[- ]budget\b", r"\bdelivery\s+cost\b", r"\bhosting\s+cost\b",
        r"\bfree\s+(?:hosting|deployment|tier|service)\b",
    ]
    for pattern in finance_patterns:
        require(re.search(pattern, public_text, re.I) is None, f"public surfaces contain no financial claim matching {pattern}")

    require('content:"";display:inline-grid' in styles or 'content: "";' in styles, "shared disclosure icon no longer depends on + text glyph metrics")
    require("linear-gradient(currentColor,currentColor) center/10px 1.5px no-repeat" in styles, "disclosure horizontal stroke is geometrically centered")
    require("linear-gradient(currentColor,currentColor) center/1.5px 10px no-repeat" in styles, "disclosure vertical stroke is geometrically centered")

    require("One mission.<br>Five ways in." in index, "homepage experience count updated to five")
    require("home-experience-card-psi" in index and 'href="psi.html"' in index, "PSI is a first-class homepage experience")
    require("Phase R — PSI homepage discovery" in landing, "PSI card participates in responsive homepage layout")

    for phrase in ["drawWaveFront", "sun-to-orion", "QUALITATIVE PROPAGATION", "space-weather-qa=1"]:
        require(phrase in weather, f"Space Weather visual contract present: {phrase}")
    require("solar-activity" not in weather and "shielding-assumption" not in weather, "old generic Space Weather controls were not restored")

    # The current engineering Entry implementation must remain byte-for-byte identical to production main.
    for path, expected in EXPECTED_ENTRY_BLOBS.items():
        require(git_blob(path) == expected, f"current Entry implementation preserved byte-for-byte: {path}")

    require('id="entry-visual-companion"' in mission, "additional Entry visual companion exists inside mission route")
    require('id="entry-flight-canvas"' in mission and 'id="entry-scrubber"' in mission and 'id="entry-play"' in mission, "current engineering Entry controls remain present")
    require('href="entry-visual.css"' in mission, "Entry visual companion stylesheet is loaded separately")
    require('src="js/entry.js"' in mission and 'src="js/entry-visual.js"' in mission, "current Entry runtime and additive visual runtime both load")
    require(mission.index('src="js/entry.js"') < mission.index('src="js/entry-visual.js"'), "additive visual loads after the current Entry runtime")

    for phrase in [
        "entry-visual-companion", "visualSequence", "space-entry-descent-parachutes-splashdown",
        "A2EntryModel", "model.stateAt", "entry-visual-scrubber", "currentSimulationPreserved",
    ]:
        require(phrase in entry_visual, f"additive Entry visual contract present: {phrase}")
    require("#entry-scrubber" in entry_visual and "!== scrubber" in entry_visual, "additive Entry QA explicitly checks independence from current engineering scrubber")
    require("entry-visual-companion" in entry_visual_css and "entry-phase-i-shell" not in entry_visual_css, "additive Entry CSS is namespaced away from current engineering simulation")

    require((ROOT / "scripts/validation/phase_r_targeted_regression.html").is_file(), "Phase R targeted browser harness exists")
    require((ROOT / "scripts/validation/validate_phase_r_targeted_regression.py").is_file(), "Phase R targeted browser gate exists")
    require((ROOT / "docs/PHASE_R_TARGETED_PUBLIC_POLISH.md").is_file(), "Phase R recovery/adaptation record exists")

    print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
