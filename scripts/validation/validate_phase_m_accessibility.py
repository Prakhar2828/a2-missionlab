from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTES = [
    "index.html",
    "mission.html",
    "windows.html",
    "gnc.html",
    "mission-control.html",
    "psi.html",
    "library.html",
    "technical-report.html",
]

failures: list[str] = []


def check(condition: bool, label: str) -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}")
        failures.append(label)


class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.images: list[dict[str, str | None]] = []
        self.canvases: list[dict[str, str | None]] = []
        self.buttons: list[dict[str, str | None]] = []
        self.navs: list[dict[str, str | None]] = []
        self.h1_count = 0
        self.main_count = 0
        self.main_ids: set[str] = set()
        self.skip_href = ""
        self.html_lang = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "html":
            self.html_lang = a.get("lang", "")
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "main":
            self.main_count += 1
            if a.get("id"):
                self.main_ids.add(a["id"])
        elif tag == "a" and "skip" in (a.get("class") or "").split():
            self.skip_href = a.get("href") or ""
        elif tag == "img":
            self.images.append(a)
        elif tag == "canvas":
            self.canvases.append(a)
        elif tag == "button":
            self.buttons.append(a)
        elif tag == "nav":
            self.navs.append(a)


def load(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


print("A2 MissionLab Phase M accessibility / responsive static validation")
print("=" * 76)

parsed: dict[str, AuditParser] = {}
for route in ROUTES:
    parser = AuditParser()
    parser.feed(load(route))
    parsed[route] = parser
    check(parser.html_lang.lower() == "en", f"{route} declares English document language")
    check(parser.main_count == 1 and len(parser.main_ids) == 1, f"{route} exposes one named main landmark")
    skip_id = parser.skip_href[1:] if parser.skip_href.startswith("#") else ""
    check(bool(skip_id) and skip_id in parser.main_ids, f"{route} skip link targets its main landmark")
    check(parser.h1_count == 1, f"{route} has one primary H1")
    check(any((n.get("aria-label") or "").strip() for n in parser.navs), f"{route} primary navigation has an accessible label")
    check(all("alt" in img for img in parser.images), f"{route} images explicitly define alt text")

# Canvas contract: decorative hero is hidden; engineering canvases are named text alternatives.
canvas_by_id: dict[str, tuple[str, dict[str, str | None]]] = {}
for route, parser in parsed.items():
    for canvas in parser.canvases:
        canvas_id = canvas.get("id") or ""
        canvas_by_id[canvas_id] = (route, canvas)
        if canvas_id == "hero-stars":
            check(canvas.get("aria-hidden") == "true", "decorative hero canvas is hidden from assistive technology")
            continue
        check(canvas.get("role") == "img", f"{route} #{canvas_id} exposes image semantics")
        check(bool((canvas.get("aria-label") or "").strip()), f"{route} #{canvas_id} has an accessible name")
        described = (canvas.get("aria-describedby") or "").split()
        if described:
            check(all(ref in parser.ids for ref in described), f"{route} #{canvas_id} text-equivalent references resolve")
        else:
            # Mission Control intentionally keeps its fallback text in the canvas element.
            check(canvas_id == "mc-canvas", f"{route} #{canvas_id} has a text-equivalent mechanism")

windows = load("windows.html")
check('id="crew-photo"' in windows and 'role="button"' not in re.search(r'<img\s+id="crew-photo"[\s\S]*?>', windows, re.I).group(0), "Windows photo remains semantic image content")
check('id="crew-photo-open"' in windows and 'aria-controls="crew-lightbox"' in windows, "Windows fullscreen action uses a real button linked to the dialog")
check('id="crew-lightbox"' in windows and '<dialog' in windows.lower(), "Windows lightbox uses native dialog semantics")

# Navigation disclosure state and ownership.
core = load("js/core.js")
library_js = load("library.js")
psi_js = load("js/psi.js")
check("setupDisclosureNav" in core and "event.key==='Escape'" in core and "returnFocus:true" in core, "shared mobile nav supports Escape and focus return")
check("libraryMenu" not in library_js and "const menu = document.querySelector('.menu-btn')" not in library_js, "Mission Library does not duplicate shared nav event ownership")
check("setNavOpen" in psi_js and "event.key==='Escape'" in psi_js and "returnFocus:true" in psi_js, "standalone PSI nav supports Escape and focus return")

# Screen-reader state for controls whose visual selection is meaningful.
trajectory = load("js/trajectory.js")
weather = load("js/space-weather.js")
entry = load("js/entry.js")
gnc = load("js/gnc.js")
windows_js = load("js/windows.js")
for path, text, token, label in [
    ("js/trajectory.js", trajectory, "aria-pressed", "trajectory preset/direction controls expose pressed state"),
    ("js/space-weather.js", weather, "aria-pressed", "space-weather preset/location controls expose pressed state"),
    ("js/psi.js", psi_js, "aria-pressed", "PSI engine/regolith controls expose pressed state"),
    ("js/gnc.js", gnc, "aria-pressed", "GNC explanatory/mode controls expose pressed state"),
    ("js/entry.js", entry, "aria-current", "Entry event rail exposes current checkpoint state"),
    ("js/windows.js", windows_js, "aria-current", "Windows filmstrip exposes current image state"),
]:
    check(token in text, label)
check("aria-valuetext" in entry, "Entry scrubber exposes time/phase/event value text")
check("aria-valuetext" in windows_js, "Windows scrubber exposes current image value text")

# Reduced motion: CSS plus nonessential shared/mission canvas RAF loops.
styles = load("styles.css") + "\n" + load("responsive-hardening.css")
mission_js = load("js/mission.js")
mission_control_js = load("js/mission-control.js")
check("prefers-reduced-motion" in styles, "shared CSS defines reduced-motion behavior")
check("reducedMotion=matchMedia('(prefers-reduced-motion: reduce)')" in core, "shared hero canvas reads reduced-motion preference")
check("missionReducedMotion=matchMedia('(prefers-reduced-motion: reduce)')" in mission_js, "Mission Explorer canvas reads reduced-motion preference")
check("prefers-reduced-motion: reduce" in psi_js, "PSI decorative particle motion reads reduced-motion preference")
check("prefers-reduced-motion: reduce" in mission_control_js, "Mission Control runtime reads reduced-motion preference")

# Focus, touch, and safe-area contracts.
windows_css = load("windows.css")
library_css = load("library.css")
responsive = load("responsive-hardening.css")
mc_regression = load("scripts/validation/mission_control_regression.html")
check(".crew-photo-open:focus-visible" in windows_css and "outline: 3px solid" in windows_css, "Windows image/lightbox affordances retain visible keyboard focus")
check(".library-filter:focus-visible{outline:3px" in library_css and ".library-result-card:focus-visible{outline:3px" in library_css, "Mission Library filters/cards retain visible keyboard focus")
check("min-height:44px" in responsive.replace(" ", ""), "responsive layer preserves >=44 px minimum control height")
check("minimumTouch < 64" in mc_regression, "Mission Control protected browser contract preserves >=64 px controls")
check("safe-area-inset-top" in responsive and "safe-area-inset-bottom" in responsive and "safe-area-inset-left" in responsive and "safe-area-inset-right" in responsive, "responsive layer handles phone safe-area insets")

# Mobile-group semantics added where selection is mutually exclusive.
mission_html = load("mission.html")
check('id="weather-presets" role="group"' in mission_html, "space-weather severity presets expose grouped semantics")
check('id="location-select" role="group"' in mission_html, "space-weather location controls expose grouped semantics")

if failures:
    print(f"\nRESULT: FAIL ({len(failures)} issue(s))")
    raise SystemExit(1)

print("\nRESULT: PASS")
