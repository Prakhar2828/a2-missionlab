from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINKEDIN = "https://www.linkedin.com/in/prakhar-pandey-470702263"
CREATOR = "Prakhar Pandey"
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
REVIEW = ROOT / "docs" / "CREATOR_CONVERSION_QA.md"
CI = ROOT / ".github" / "workflows" / "ci.yml"
PUBLIC_VALIDATOR = ROOT / "scripts" / "validate_public_experience.py"
README = ROOT / "README.md"


class CreatorHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.author_meta: list[str] = []
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        data = dict(attrs)
        if tag == "meta" and data.get("name", "").lower() == "author":
            self.author_meta.append(data.get("content", ""))
        if tag == "a":
            self.links.append(data)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"CREATOR CONVERSION VALIDATION FAILED: {message}")
    print("PASS:", message)


def read(path: Path) -> str:
    require(path.is_file(), f"required creator-conversion artifact exists: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    print("A2 MissionLab creator identity / executive conversion validation")
    print("=" * 78)

    pages: dict[str, str] = {}
    parsers: dict[str, CreatorHTMLParser] = {}
    for route in MAJOR_ROUTES:
        text = read(ROOT / route)
        parser = CreatorHTMLParser()
        parser.feed(text)
        pages[route] = text
        parsers[route] = parser

        require(CREATOR in text, f"creator identity is visible on {route}")
        require(parser.author_meta == [CREATOR], f"{route} exposes exactly one creator author meta tag")
        linkedin_links = [link for link in parser.links if link.get("href") == LINKEDIN]
        require(linkedin_links, f"{route} exposes the exact LinkedIn contact path")
        for link in linkedin_links:
            rel = set(link.get("rel", "").split())
            require(link.get("target") == "_blank", f"{route} LinkedIn opens as an explicit external path")
            require({"noopener", "noreferrer"}.issubset(rel), f"{route} LinkedIn link uses safe external-link rel tokens")
            classes = set(link.get("class", "").split())
            require("x-button" not in classes and "nav-cta" not in classes,
                    f"{route} LinkedIn is not promoted to a primary CTA")

    index = pages["index.html"]
    report = pages["technical-report.html"]
    readme = read(README)
    review = read(REVIEW)
    ci = read(CI)
    public_validator = read(PUBLIC_VALIDATOR)

    require("Independent Artemis II engineering reconstruction" in index,
            "homepage first-view hierarchy establishes independent engineering status")
    require('class="x-creator-line"' in index and "Built independently by" in index,
            "homepage includes the restrained creator credit")
    require('class="home-engineering-ownership"' in index,
            "homepage includes explicit engineering-ownership proof")
    for phrase in [
        "public-data ingestion and normalization",
        "mission geometry and analysis",
        "bounded engineering models",
        "interactive simulations",
        "evidence architecture",
        "validation",
        "publication",
        "NASA/ESA data, imagery, and source material remain externally attributed",
    ]:
        require(phrase in index, f"homepage engineering ownership preserves scope/boundary: {phrase}")

    require('class="creator-byline"' in report and "Built independently by" in report,
            "Technical Report carries an engineering-study creator byline")
    require("NASA/ESA source material retains its original ownership and attribution" in report,
            "Technical Report retains external source ownership boundary")
    require(f"[Prakhar Pandey]({LINKEDIN})" in readme,
            "README identifies the creator with the exact LinkedIn path")
    require("NASA/ESA source material remains externally attributed" in readme,
            "README separates creator-built engineering from source ownership")

    public_text = "\n".join(pages.values()) + "\n" + readme
    forbidden = [
        "hire me",
        "open to work",
        "seeking opportunities",
        "download resume",
        "download résumé",
        "my resume",
        "my résumé",
    ]
    for phrase in forbidden:
        require(phrase not in public_text.lower(), f"job-seeker portfolio language remains absent: {phrase}")

    require(index.count(CREATOR) <= 3, "homepage creator naming remains deliberately bounded")
    for route in MAJOR_ROUTES[1:]:
        require(pages[route].count(CREATOR) <= 3, f"{route} creator naming remains deliberately bounded")

    reviewer_headings = [
        "SpaceX technical leadership",
        "Blue Origin technical leadership",
        "NASA engineering leadership",
        "Mission control / flight operations",
        "GNC engineer",
        "EDL engineer",
        "Principal flight/software engineer",
        "Technical recruiter",
        "Skeptical engineering hiring manager",
        "Senior executive with only 60 seconds",
    ]
    for reviewer in reviewer_headings:
        require(f"— {reviewer}" in review, f"separate creator-conversion review recorded: {reviewer}")

    for phrase in [
        "Would they know this was independently built?",
        "Would they know the builder is Prakhar Pandey?",
        "Could they reach Prakhar in one click?",
        "Does MissionLab still feel like a serious engineering product rather than a job-seeker portfolio?",
        "does not claim that creator attribution can guarantee a hiring outcome",
    ]:
        require(phrase in review, f"final adversarial boundary recorded: {phrase}")

    require("python scripts/validation/validate_creator_conversion.py" in ci,
            "CI runs the creator-conversion static gate")
    require("validate_creator_conversion.py" in public_validator,
            "public release validation requires the creator-conversion gate")
    require("CREATOR_CONVERSION_QA.md" in public_validator,
            "public release validation requires the creator-conversion review record")

    print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
