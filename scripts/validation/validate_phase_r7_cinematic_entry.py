from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ENTRY_MODEL_BLOB = "169c860861d1b34f47f4a6349b8000e012ef12bb"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def git_blob(path: str) -> str:
    return subprocess.check_output(["git", "hash-object", path], cwd=ROOT, text=True).strip()


def main() -> int:
    entry_runtime = (ROOT / "js/entry.js").read_text(encoding="utf-8")
    entry_css = (ROOT / "entry.css").read_text(encoding="utf-8")
    visual = (ROOT / "js/entry-visual.js").read_text(encoding="utf-8")
    css = (ROOT / "entry-visual.css").read_text(encoding="utf-8")
    mission = (ROOT / "mission.html").read_text(encoding="utf-8")

    print("A2 MissionLab Phase R7 cinematic additive Entry validation")
    print("=" * 76)

    require(git_blob("js/entry-model.js") == ENTRY_MODEL_BLOB, "protected Entry flight-derived model remains byte-for-byte unchanged")
    require("entryPlaybackProfile='r8-cinematic-paced'" in entry_runtime, "R8 presentation cadence is present without changing the model")
    require("Phase R8 engineering viewport-fit" in entry_css, "R8 engineering viewport-fit presentation is present")

    require('id="entry-visual-companion"' in mission, "additive visual companion remains mounted separately")
    require('<script src="js/entry.js"></script>' in mission and '<script src="js/entry-visual.js"></script>' in mission, "current Entry runtime and cinematic additive runtime both remain loaded")
    require(mission.index('<script src="js/entry.js"></script>') < mission.index('<script src="js/entry-visual.js"></script>'), "cinematic additive runtime still loads after current Entry runtime")

    required_tokens = [
        "cinematicVersion = 'r7'",
        "cinematicRevision = R8.version",
        "cameraContinuous",
        "surfaceContext",
        "oceanVisible",
        "drawSpaceEarth",
        "drawEntryHorizon",
        "drawAtmosphericWorld",
        "drawOceanRecoveryWorld",
        "drawPlasma",
        "drawParachuteSystem",
        "drawSplashAndFloat",
        "playbackFactor",
        "earthContext",
        "oceanRecovery",
        "capsuleAfloat",
        "ILLUSTRATIVE CAMERA",
        "NOT AN OFFICIAL SPLASHDOWN CAMERA VIEW",
    ]
    for token in required_tokens:
        require(token in visual, f"cinematic visual contract present: {token}")

    require("mode === 'ocean'" in visual and "earthContext = mode === 'space' || mode === 'entry' ? 'curved-limb' : 'none'" in visual, "Earth curvature is restricted to space/entry and removed for ocean recovery")
    require("R8.oceanRevealStart" in visual and "surfaceContext" in visual, "R8 separates high-altitude descent, parachutes, distant ocean approach, and splashdown")
    require("root.dataset.parachuteMode" in visual, "parachute phase is surfaced for browser QA")
    require("root.dataset.plasmaActive" in visual, "plasma/heating phase is surfaced for browser QA")
    require("root.dataset.currentSimulationPreserved = 'true'" in visual, "cinematic companion explicitly preserves current simulation boundary")
    require("$('#entry-scrubber') !== scrubber" in visual and "$('#entry-flight-canvas') !== canvas" in visual, "cinematic companion retains independent controls/canvas QA")

    require(".entry-visual-companion" in css and ".entry-visual-stage" in css, "R7 CSS remains namespaced to additive companion")
    require("min-height:650px" in css, "desktop cinematic stage receives immersive height")
    require("backdrop-filter:blur(14px)" in css, "cinematic stage badge uses premium glass treatment")
    require("@media(max-width:700px)" in css and "@media(max-width:430px)" in css, "cinematic companion retains mobile responsive contracts")
    require("@media(prefers-reduced-motion:reduce)" in css, "R7 respects reduced-motion presentation")

    # Keep deterministic rendering and reject unsupported positive camera/attitude claims.
    # The phrase "as-flown camera" is intentionally allowed exactly once inside an
    # explicit negation/evidence-boundary sentence; rejecting the substring itself
    # would punish the disclaimer that prevents overclaiming.
    lower_visual = visual.lower()
    forbidden = [
        "Math.random(",
        "official NASA camera",
        "exact attitude",
    ]
    for token in forbidden:
        require(token.lower() not in lower_visual, f"visual avoids unsupported/non-deterministic token: {token}")

    boundary = "without presenting the scene as telemetry or an as-flown camera view"
    require(
        lower_visual.count("as-flown camera") == 1 and boundary in lower_visual,
        "as-flown camera wording appears only inside the explicit non-telemetry evidence boundary",
    )

    print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
