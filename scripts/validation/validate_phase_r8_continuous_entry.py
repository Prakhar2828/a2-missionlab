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
    return subprocess.check_output(["git", "hash-object", "--", path], cwd=ROOT, text=True).strip()


def main() -> int:
    entry = (ROOT / "js/entry.js").read_text(encoding="utf-8")
    entry_css = (ROOT / "entry.css").read_text(encoding="utf-8")
    visual = (ROOT / "js/entry-visual.js").read_text(encoding="utf-8")
    visual_css = (ROOT / "entry-visual.css").read_text(encoding="utf-8")

    print("A2 MissionLab Phase R8 continuous EDL cinematic + viewport validation")
    print("=" * 78)

    require(git_blob("js/entry-model.js") == ENTRY_MODEL_BLOB, "flight-derived Entry model remains byte-for-byte unchanged")

    require("entryPlaybackProfile='r8-cinematic-paced'" in entry, "engineering playback cadence is explicitly R8 paced")
    require("entry-stage-live-controls" in entry, "engineering stage receives immediate in-view play/reset controls")
    require("entry-stage-play" in entry and "entry-stage-reset" in entry, "engineering stage control IDs are present")
    require("stage.scrollIntoView" in entry, "lower controller Play returns the engineering stage into view before playback")
    require("dt*.18" not in entry, "old ~4.5 second engineering playback cadence is removed")
    require("t<240?.018:t<569?.028:t<629?.014:t<810?.018:.010" in entry, "engineering playback uses watchable phase-aware timing")

    require("Phase R8 engineering viewport-fit" in entry_css, "viewport-fit engineering CSS marker is present")
    require("grid-template-rows:auto minmax(0,1fr) auto" in entry_css, "engineering stage chrome/canvas/note use non-overlapping rows")
    require(".entry-stage-topline{position:relative" in entry_css, "engineering top cards no longer overlay the graph")
    require(".entry-stage-note{position:relative" in entry_css, "loft/rebound note no longer overlays the graph")
    require(".entry-state-board{height:var(--entry-r8-stage-h)" in entry_css, "desktop state board is height-capped with the stage")
    require("overflow-y:auto" in entry_css, "desktop state board can scroll internally instead of stretching the graph")

    required_visual = [
        "const R8 = Object.freeze",
        "cinematicRevision = R8.version",
        "cameraContinuous",
        "transitionBlend",
        "surfaceContext",
        "oceanVisible",
        "R8.oceanRevealStart",
        "postSplashMs",
        "recoveryHoldMs",
        "drawAtmosphericWorld",
        "drawParachuteSystem",
        "drawSplashAndFloat",
    ]
    for token in required_visual:
        require(token in visual, f"continuous cinematic contract present: {token}")

    require("if (t < EVENTS.surface) return 'main';" in visual and "return 'ocean';" in visual, "ocean recovery begins only at derived surface crossing")
    require("scrubber.step = 'any'" in visual, "visual scrubber can reach the exact derived surface-crossing boundary without 0.1 s quantization")
    require("mode === 'main' ? smoother(remap(t, R8.oceanRevealStart, EVENTS.surface - 5)) : 0" in visual, "ocean is withheld from descent/drogue and revealed only late in main descent")
    require("surfaceContext = oceanAlpha > .08 ? 'distant-ocean' : 'cloud-deck'" in visual, "descent/recovery surface context distinguishes cloud deck from distant ocean")
    require("const mainDeploy = smoother(remap(visualT, EVENTS.main, EVENTS.main + 24))" in visual, "main parachutes deploy progressively instead of appearing as a freeze frame")
    require("const drogueFade = 1 - smoother(remap(visualT, EVENTS.main, EVENTS.main + 14))" in visual, "drogue-to-main handoff crossfades continuously")
    require("R8.recoveryHoldMs" in visual and "postSplashMs = Math.min" in visual, "splashdown includes a real-time recovery hold instead of ending instantly")
    require("cinematicVersion = 'r7'" in visual, "R7 browser contract remains backward compatible")
    require("version: 'r8'" in visual, "R8 revision is explicitly surfaced")

    require("Phase R8 continuous cinematic pass" in visual_css, "R8 cinematic CSS pass is present")
    require("@media(max-width:700px)" in visual_css and "@media(max-width:430px)" in visual_css, "cinematic companion remains responsive")

    require("Math.random(" not in visual, "continuous cinematic render remains deterministic")
    require("official NASA camera" not in visual.lower(), "no unsupported official-camera claim is introduced")
    require("exact attitude" not in visual.lower(), "no unsupported exact-attitude claim is introduced")

    print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
