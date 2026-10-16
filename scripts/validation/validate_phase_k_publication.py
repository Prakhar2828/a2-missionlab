from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START = "c7758aa415928467da0ebb6e48c276c1082be566"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def main() -> int:
    report = (ROOT / "technical-report.html").read_text(encoding="utf-8")
    report_css = (ROOT / "report.css").read_text(encoding="utf-8")
    library = (ROOT / "library.html").read_text(encoding="utf-8")
    library_js = (ROOT / "library.js").read_text(encoding="utf-8")
    library_css = (ROOT / "library.css").read_text(encoding="utf-8")

    print("A2 MissionLab Phase K publication / knowledge-system validation")
    print("=" * 72)

    require('href="report.css"' in report, "Technical Report uses dedicated publication CSS")
    require('id="executive-summary"' in report, "Technical Report has an executive summary")
    require("Study baseline" not in report, "Technical Report no longer publishes a visible Study baseline field")
    require(START not in report, "Technical Report no longer exposes the raw Phase J baseline hash")
    require("Static GitHub Pages deployment" in report, "Technical Report retains deployment architecture without a cost claim")
    require(report.count('class="tech-figure" id="fig-') == 13, "Technical Report has 13 stable figure anchors")
    require(len(re.findall(r'<table id="table-[^"]+"><caption>Table [123]\.', report)) == 3, "Technical Report has 3 numbered/anchored tables")
    require('<script src="app.js"></script>' not in report, "obsolete app.js is not loaded by Technical Report")
    require("public-experience-v3" not in report, "Technical Report repository links are not pinned to the obsolete public-experience-v3 branch")
    require("/feature/artemis-ii-preliminary-lunar-science-report/" in report, "current Artemis II preliminary science landing page is linked")
    require("/mission/artemis-iv/" in report, "current Artemis IV mission page is linked")
    require("@media print" in report_css and "@page" in report_css, "Technical Report has explicit print/PDF styling")
    require('id="eq-sutton-graves"' in report and "equation-number" in report, "Technical Report numbers the Sutton–Graves equation")
    require('<h2 id="sources">References and artifact ledger</h2>' in report and '<ol class="source-list">' in report, "Technical Report uses a formal ordered reference/artifact ledger")

    figure_paths = re.findall(r'<figure class="tech-figure"[^>]*><img src="([^"]+)"', report)
    require(len(figure_paths) == 13, "Technical Report retains exactly 13 engineering figures")
    missing = [path for path in figure_paths if not (ROOT / path).is_file()]
    require(not missing, "all Technical Report figure assets resolve locally")

    require('href="library.css"' in library, "Mission Library uses dedicated knowledge-system CSS")
    for token in ["library-categories", "library-result-count", "library-results"]:
        require(f'id="{token}"' in library, f"Mission Library exposes {token}")

    topic_ids = re.findall(r"\bid:'([^']+)'", library_js)
    question_ids = re.findall(r"^\s*'([^']+)':'.*'", library_js[library_js.index("const questionById"):library_js.index("const categoryOrder")], re.M)
    category_section = library_js[library_js.index("const categoryById"):library_js.index("const questionById")]
    category_ids = re.findall(r"'([^']+)':'[^']+'", category_section)
    require(len(topic_ids) == 28 and len(set(topic_ids)) == 28, "Mission Library retains 28 unique deep dives")
    require(set(question_ids) == set(topic_ids), "every Mission Library deep dive has a curated engineering question")
    require(set(category_ids) == set(topic_ids), "every Mission Library deep dive has a canonical category")
    require("const categoryOrder=['All','Flight Dynamics','Vehicle & GNC','Mission Operations','Entry & Recovery','Environment & Radiation','Lunar Science','Data & Software','Evidence & Methods','Future Artemis'];" in library_js, "Mission Library exposes the canonical Phase K category system")
    require("content.innerHTML=shown.map(article).join('')" not in library_js, "Mission Library no longer renders all matching full articles at once")
    require("content.innerHTML=article(selected)" in library_js, "Mission Library renders one focused deep dive at a time")
    require("knowledge-path" in library_js and "Question</span><span>Explanation</span><span>Evidence</span><span>Source" in library_js, "QUESTION → EXPLANATION → EVIDENCE → SOURCE path is explicit")
    require("relatedTopics" in library_js and "related-topics" in library_js, "Mission Library provides related-question discovery")
    require(START in library_js and "public-experience-v3" not in library_js, "Mission Library repository evidence is pinned to the Phase J study baseline")
    require("loading=\"lazy\"" in library_js, "Mission Library deep-dive figures are lazy-loaded")
    require(".library-result-card" in library_css and ".knowledge-path" in library_css, "Mission Library has dedicated browse/read visual states")

    print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
