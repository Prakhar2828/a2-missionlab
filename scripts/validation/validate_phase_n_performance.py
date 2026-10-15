from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
failures: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("PASS: " if condition else "FAIL: ") + message)
    if not condition:
        failures.append(message)


def load(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class ImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: list[dict[str, str]] = []
        self.preconnects: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        data = dict(attrs)
        if tag == "img":
            self.images.append(data)
        if tag == "link" and data.get("rel") == "preconnect":
            self.preconnects.append(data.get("href", ""))


def parse(path: str) -> ImageParser:
    parser = ImageParser()
    parser.feed(load(path))
    return parser


print("A2 MissionLab Phase N performance / loading / failure-state static validation")
print("=" * 82)

required = [
    "docs/PHASE_N_PERFORMANCE_QA.md",
    "scripts/validation/validate_phase_n_performance.py",
    "scripts/validation/phase_n_performance_regression.html",
    "scripts/validation/validate_phase_n_regression.py",
]
for path in required:
    check((ROOT / path).is_file(), f"required Phase N artifact exists: {path}")

core = load("js/core.js")
mission = load("js/mission.js")
gnc = load("js/gnc.js")
windows = load("js/windows.js")
trajectory = load("js/trajectory.js")
weather = load("js/space-weather.js")
mission_control = load("js/mission-control.js")
styles = load("styles.css")
public_validator = load("scripts/validate_public_experience.py")
browser_harness = load("scripts/validation/phase_n_performance_regression.html")
browser_driver = load("scripts/validation/validate_phase_n_regression.py")

earth = ROOT / "assets/public/celestial/earth_pia18033.jpg"
moon = ROOT / "assets/public/celestial/moon_lro_mosaic.jpg"
combined = earth.stat().st_size + moon.stat().st_size
check(combined == 771072, f"celestial optional payload baseline remains 771,072 bytes (found {combined:,})")
check("status:'idle'" in core and "ensureCelestialImage" in core, "celestial JPEGs are demand-owned from an idle state")
check("loadCelestialImage(" not in core, "core no longer performs eager global celestial image loads")
check(core.count("assets/public/celestial/earth_pia18033.jpg") == 1, "Earth JPEG has one lazy source owner")
check(core.count("assets/public/celestial/moon_lro_mosaic.jpg") == 1, "Moon JPEG has one lazy source owner")
check("new Event('a2:celestialchange')" in core, "celestial completion uses a targeted redraw event instead of fake resize")
for path, text in [
    ("js/mission.js", mission),
    ("js/trajectory.js", trajectory),
    ("js/space-weather.js", weather),
    ("js/mission-control.js", mission_control),
]:
    check("a2:celestialchange" in text, f"{path} redraws when a demanded celestial asset resolves")

mission_size = (ROOT / "js/mission.js").stat().st_size
check(mission_size < 22000, f"mission.js dead-code removal keeps route runtime below 22 KB (found {mission_size:,} bytes)")
check("data-entry-phase-i" not in mission, "bypassed pre-Phase-I Entry renderer is removed from mission.js")
check("entryStates" not in mission and "entryCanvas" not in mission, "legacy Entry state/RAF implementation is no longer shipped")

check("IntersectionObserver" in mission and "missionInView" in mission, "Mission Explorer has viewport-aware animation ownership")
check("document.hidden" in mission and "missionReducedMotion" in mission, "Mission Explorer preserves hidden-document and reduced-motion suspension")
check("dataset.a2Animation" in mission, "Mission Explorer exposes deterministic running/paused QA state")
check("IntersectionObserver" in gnc and "canvasInView" in gnc, "GNC has viewport-aware animation ownership")
check("document.hidden" in gnc and "last=0" in gnc, "GNC pauses hidden/offscreen work without frame-time catch-up")
check("dataset.a2Animation" in gnc, "GNC exposes deterministic running/paused QA state")
check("placeRouteElement" in browser_harness and "scrollBehavior='auto'" in browser_harness, "Phase N browser harness establishes route-local visibility positions deterministically")
check("scrollIntoView({" not in browser_harness, "Phase N browser harness avoids nested-iframe scrollIntoView ambiguity")
check("isRouteFarOffscreen" in browser_harness and "isRouteVisible" in browser_harness, "Phase N browser harness couples RAF state assertions to measured route geometry")
check("placeRouteElement(win,doc,figure,'visible')" in browser_harness and "phase-n-intentional-missing-figure.svg" in browser_harness, "Phase N missing-image regression makes the lazy figure visible before injecting the missing resource")
check("DOM readiness timeout loading" in browser_harness and "frame.onload" not in browser_harness, "Phase N harness uses local DOM readiness instead of remote-image-sensitive window.load")
check("__phase_n_result__" in browser_harness and "__phase_n_result__" in browser_driver, "Phase N browser and Python driver use an explicit completion handshake")
check("subprocess.Popen" in browser_driver and "result_event.wait" in browser_driver, "Phase N Python driver waits for browser completion instead of dump-dom timing")
check("--dump-dom" not in browser_driver and "--virtual-time-budget" not in browser_driver, "Phase N release gate no longer depends on dump-dom virtual-time completion")

check("queueCrewGeometryResize" in windows, "Windows keeps RAF-coalesced crew geometry resize ownership")
check("window.addEventListener('resize',()=>drawCrewGeometry" not in windows, "Windows duplicate direct resize redraw is removed")

check("document.addEventListener('error'" in core and ",true);" in core, "shared runtime captures present and future image failures")
check("a2-image-failure" in core and "a2-image-unavailable" in core, "shared runtime replaces broken local images with explicit fallback state")
check(".a2-image-failure" in styles, "shared stylesheet presents explicit image failure state")
check("drawEarthProcedural" in core and "drawMoonProcedural" in core, "procedural celestial fallbacks remain available")

route_expectations = {
    "mission.html": 7,
    "gnc.html": 1,
    "mission-control.html": 1,
    "technical-report.html": 13,
}
for route, expected in route_expectations.items():
    parser = parse(route)
    lazy = [img for img in parser.images if img.get("loading") == "lazy" and img.get("decoding") == "async"]
    check(len(parser.images) == expected, f"{route} image count remains {expected}")
    check(len(lazy) == expected, f"{route} defers all below-fold/static figures with lazy async decoding")

index = parse("index.html")
check(len(index.images) == 9, "homepage retains nine intended mission images")
check(index.images[0].get("fetchpriority") == "high" and index.images[0].get("decoding") == "async", "homepage hero remains explicitly high-priority")
check(all(img.get("loading") == "lazy" and img.get("decoding") == "async" for img in index.images[1:]), "homepage non-hero imagery is lazy async")

windows_page = parse("windows.html")
local_windows = [img for img in windows_page.images if img.get("src", "").startswith("docs/assets/")]
check(all(img.get("loading") == "lazy" and img.get("decoding") == "async" for img in local_windows), "Windows lower-page local figures are lazy async")
check(any(img.get("id") == "crew-photo" and img.get("loading") != "lazy" for img in windows_page.images), "Windows primary current image remains eager")

for route in ["mission.html", "gnc.html", "mission-control.html"]:
    parser = parse(route)
    check("https://images-assets.nasa.gov" not in parser.preconnects, f"{route} removes unused NASA image preconnect")

check("validate_phase_n_performance.py" in public_validator and "phase_n_performance_regression.html" in public_validator, "public release validator requires Phase N QA artifacts")

if failures:
    print(f"\nRESULT: FAIL ({len(failures)} issue(s))")
    raise SystemExit(1)

print("\nRESULT: PASS")
