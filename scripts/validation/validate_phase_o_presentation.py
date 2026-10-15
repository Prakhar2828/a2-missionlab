from __future__ import annotations

import re
import struct
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://prakhar2828.github.io/a2-missionlab/"
SOCIAL_URL = BASE + "docs/assets/social/a2-missionlab-social-preview.png"
SOCIAL_PATH = ROOT / "docs/assets/social/a2-missionlab-social-preview.png"
SOCIAL_SOURCE = ROOT / "docs/assets/social/a2-missionlab-social-preview.svg"

ROUTES = {
    "index.html": {
        "title": "A2 MissionLab — Artemis II Engineering Reconstruction",
        "description": "Explore Artemis II through public mission data, deterministic engineering models, Mission Control reasoning, crew imagery, GNC, entry, space weather, and evidence-aware analysis.",
        "canonical": BASE,
        "type": "website",
    },
    "mission.html": {
        "title": "Mission Explorer — A2 MissionLab",
        "description": "Explore Artemis II trajectory, correction maneuvers, entry and recovery, and space-weather context through evidence-bounded public-data reconstruction.",
        "canonical": BASE + "mission.html",
        "type": "website",
    },
    "windows.html": {
        "title": "Through Orion's Windows — A2 MissionLab",
        "description": "Explore 25 evidence-labeled Artemis II mission images with crew-view context, geometry, provenance, and direct NASA source links.",
        "canonical": BASE + "windows.html",
        "type": "website",
    },
    "gnc.html": {
        "title": "Guidance, Navigation & Control — A2 MissionLab",
        "description": "Explore public Artemis II GNC architecture through a simplified proximity-operations teaching model with auto, manual, and disturbance modes.",
        "canonical": BASE + "gnc.html",
        "type": "website",
    },
    "mission-control.html": {
        "title": "Mission Control — A2 MissionLab",
        "description": "Explore Artemis II Mission Control reasoning through discipline lenses, public mission scenarios, evidence boundaries, and decision reconstruction.",
        "canonical": BASE + "mission-control.html",
        "type": "website",
    },
    "psi.html": {
        "title": "Plume-Surface Interaction — A2 MissionLab",
        "description": "Explore future-Artemis plume-surface interaction through an evidence-bounded educational model of geometry, regolith response, ejecta, and hardware exposure.",
        "canonical": BASE + "psi.html",
        "type": "website",
    },
    "library.html": {
        "title": "Mission Library — A2 MissionLab",
        "description": "Search an evidence-aware Artemis II engineering knowledge base spanning flight dynamics, GNC, communications, entry, science, Mission Control, and data methods.",
        "canonical": BASE + "library.html",
        "type": "website",
    },
    "technical-report.html": {
        "title": "Technical Report — A2 MissionLab",
        "description": "Read the A2 MissionLab technical report on reconstructing Artemis II from public data using flight dynamics, mission operations, environmental modeling, and explicit evidence boundaries.",
        "canonical": BASE + "technical-report.html",
        "type": "article",
    },
}


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.meta_name: dict[str, list[str]] = {}
        self.meta_property: dict[str, list[str]] = {}
        self.links: dict[str, list[dict[str, str]]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            if a.get("name"):
                self.meta_name.setdefault(a["name"].lower(), []).append(a.get("content", ""))
            if a.get("property"):
                self.meta_property.setdefault(a["property"].lower(), []).append(a.get("content", ""))
        elif tag == "link" and a.get("rel"):
            for token in a["rel"].lower().split():
                self.links.setdefault(token, []).append(a)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return "".join(self.title_parts).strip()


def parse_route(name: str) -> HeadParser:
    parser = HeadParser()
    parser.feed((ROOT / name).read_text(encoding="utf-8"))
    return parser


def single(values: list[str] | None) -> str | None:
    if not values or len(values) != 1:
        return None
    return values[0]


def png_dimensions(path: Path) -> tuple[int, int]:
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
        raise ValueError("invalid PNG signature/IHDR")
    return struct.unpack(">II", raw[16:24])


failures: list[str] = []


def check(ok: bool, label: str) -> None:
    if ok:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}")
        failures.append(label)


print("A2 MissionLab Phase O presentation / metadata validation")
print("=" * 76)

for route, expected in ROUTES.items():
    parser = parse_route(route)
    check(parser.title == expected["title"], f"{route} has the deliberate document title")
    check(single(parser.meta_name.get("description")) == expected["description"], f"{route} has one exact meta description")
    canonical_links = parser.links.get("canonical", [])
    check(len(canonical_links) == 1 and canonical_links[0].get("href") == expected["canonical"], f"{route} has one exact canonical URL")
    check(single(parser.meta_property.get("og:site_name")) == "A2 MissionLab", f"{route} Open Graph site name")
    check(single(parser.meta_property.get("og:title")) == expected["title"], f"{route} Open Graph title")
    check(single(parser.meta_property.get("og:description")) == expected["description"], f"{route} Open Graph description")
    check(single(parser.meta_property.get("og:type")) == expected["type"], f"{route} Open Graph type")
    check(single(parser.meta_property.get("og:url")) == expected["canonical"], f"{route} Open Graph URL matches canonical")
    check(single(parser.meta_property.get("og:image")) == SOCIAL_URL, f"{route} uses the repository-owned social image")
    check(single(parser.meta_property.get("og:image:width")) == "1200" and single(parser.meta_property.get("og:image:height")) == "630", f"{route} declares social image dimensions")
    check(single(parser.meta_property.get("og:image:alt")) == "A2 MissionLab — public-data Artemis II engineering reconstruction", f"{route} declares social image alt text")
    check(single(parser.meta_name.get("twitter:card")) == "summary_large_image", f"{route} uses large Twitter/X card")
    check(single(parser.meta_name.get("twitter:title")) == expected["title"], f"{route} Twitter/X title")
    check(single(parser.meta_name.get("twitter:description")) == expected["description"], f"{route} Twitter/X description")
    check(single(parser.meta_name.get("twitter:image")) == SOCIAL_URL, f"{route} Twitter/X image")
    icons = parser.links.get("icon", [])
    icon_hrefs = {entry.get("href") for entry in icons}
    check({"favicon.svg", "favicon.ico"}.issubset(icon_hrefs), f"{route} retains SVG + ICO favicons")

check(SOCIAL_PATH.is_file(), "repository-owned PNG social preview exists")
check(SOCIAL_SOURCE.is_file(), "editable SVG social-preview source exists")
if SOCIAL_PATH.is_file():
    try:
        width, height = png_dimensions(SOCIAL_PATH)
        check((width, height) == (1200, 630), f"social preview is exactly 1200×630 (found {width}×{height})")
    except Exception as exc:
        check(False, f"social preview PNG is valid ({exc})")
if SOCIAL_SOURCE.is_file():
    source = SOCIAL_SOURCE.read_text(encoding="utf-8")
    check("A2 MissionLab" in source and "PUBLIC-DATA ENGINEERING RECONSTRUCTION" in source, "social SVG communicates project identity without official-NASA claim")
    clean_source = source.replace("http://www.w3.org/2000/svg", "")
    check("http://" not in clean_source and "https://" not in clean_source, "social SVG has no third-party runtime image dependency")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
required_readme_sections = [
    "## Why MissionLab exists",
    "## Mission experiences",
    "## Data and evidence",
    "## Architecture",
    "## Simulation methodology",
    "## Selected results",
    "## Validation",
    "## Demo media",
    "## Run locally",
    "## Zero-cost architecture",
    "## Technical challenges",
    "## Limitations",
    "## Project status",
]
for heading in required_readme_sections:
    check(heading in readme, f"README includes {heading[3:]}")

for phrase in [
    "Phases 0 through 9 are complete",
    "Evidence-Grounded Mission Analyst",
    "MISSIONLAB DERIVED",
    "PUBLIC EVENT SEQUENCE",
    "TEMPORAL SEQUENCE",
    "DISCIPLINE RELEVANCE",
    "TROUBLESHOOTING ACTION",
    "UNKNOWN PUBLIC FACT",
    "docs/assets/a2-missionlab-release-overview.svg",
    "docs/assets/social/a2-missionlab-social-preview.png",
    BASE,
    "$0 ongoing cost",
]:
    check(phrase in readme, f"README preserves required presentation/evidence phrase: {phrase}")

for forbidden in [
    r"official NASA application",
    r"flight-qualified simulation",
    r"private telemetry replay",
    r"reconstructs private mission control",
]:
    if forbidden == r"official NASA application":
        # The disclaimer must explicitly negate this phrase.
        check("not an official nasa application" in readme.lower(), "README explicitly disclaims official NASA status")
    else:
        check(re.search(forbidden, readme, re.I) is None, f"README avoids oversell phrase: {forbidden}")

public_validator = (ROOT / "scripts/validate_public_experience.py").read_text(encoding="utf-8")
for artifact in [
    "validate_phase_o_presentation.py",
    "phase_o_presentation_regression.html",
    "validate_phase_o_regression.py",
    "PHASE_O_PRESENTATION_QA.md",
    "a2-missionlab-social-preview.png",
]:
    check(artifact in public_validator, f"public release validator requires Phase O artifact: {artifact}")

ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
check("python scripts/validation/validate_phase_o_presentation.py" in ci, "portable CI runs the Phase O static presentation gate")
check("validate_phase_o_regression.py" not in ci, "portable CI does not falsely claim the Windows Edge/Chrome Phase O browser gate")

if failures:
    print(f"\nRESULT: FAIL ({len(failures)} issue(s))")
    raise SystemExit(1)

print("\nRESULT: PASS")
