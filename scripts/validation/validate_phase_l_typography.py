from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTES = {
    "index.html": "landing.css",
    "mission.html": "entry.css",
    "windows.html": "windows.css",
    "gnc.html": "gnc.css",
    "mission-control.html": "mission-control.css",
    "psi.html": "psi.css",
    "library.html": "library.css",
    "technical-report.html": "report.css",
}

failures: list[str] = []

def check(ok: bool, label: str) -> None:
    if ok:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}")
        failures.append(label)

styles = (ROOT / "styles.css").read_text(encoding="utf-8")
typography = (ROOT / "typography.css").read_text(encoding="utf-8")

print("A2 MissionLab Phase L typography / visual-quality validation")
print("=" * 72)

check("font-family:Inter" not in styles.replace(" ", ""), "unresolved Inter body request removed")
check("--font-sans:system-ui" in styles.replace(" ", ""), "deliberate system-ui-first sans stack")
check("--font-mono:ui-monospace" in styles.replace(" ", ""), "deliberate system monospace stack")
check("@font-face" not in typography.lower(), "no bundled font-face dependency")
check("fonts.googleapis" not in typography.lower() and "fonts.gstatic" not in typography.lower(), "no remote font-service dependency")
# Runtime dependency check, not a repository-wide filesystem census.
# Development environments (for example .venv packages such as Matplotlib) may
# legitimately carry their own font resources; Phase L only guarantees that the
# public static application does not reference or require a font binary.
public_runtime_files = [ROOT / route for route in ROUTES]
public_runtime_files += sorted(ROOT.glob("*.css"))
font_binary_ref = re.compile(r"(?i)\.(?:woff2?|ttf|otf)(?:[?#)\"']|$)")
font_binary_refs: list[str] = []
for runtime_file in public_runtime_files:
    text = runtime_file.read_text(encoding="utf-8")
    if font_binary_ref.search(text):
        font_binary_refs.append(runtime_file.relative_to(ROOT).as_posix())
check(not font_binary_refs, "public typography requires no repository font binaries")
check("background:" not in typography and "color:" not in typography, "Phase L typography layer does not repaint route identity")
check(".x-intro h1" in typography and "font-size: clamp(3rem,6vw,6.4rem)" in typography, "intro H1 hierarchy is explicit")
check(".x-hero h1" in typography and "line-height: .87" in typography, "cinematic hero compression is normalized")
check(".gnc-page #gnc-lab .x-section-head h2" in typography and ".mission-control-page #mission-control .x-section-head h2" in typography, "GNC and Mission Control display hierarchy normalized")
check("font-variant-numeric: tabular-nums lining-nums" in typography, "engineering readouts use tabular lining numerals")
check(".equation" in typography and 'Georgia,"Times New Roman",serif' in typography, "mathematical serif voice preserved")
check("@media print" in typography and "font-family: Georgia" in typography, "Technical Report print serif contract preserved")
check("@media (max-width: 760px)" in typography, "mobile display typography receives explicit treatment")

for route, identity_css in ROUTES.items():
    text = (ROOT / route).read_text(encoding="utf-8")
    links = re.findall(r'<link\s+rel="stylesheet"\s+href="([^"]+\.css)"', text, flags=re.I)
    check(bool(links) and links[-1] == "typography.css", f"{route} loads typography.css last")
    check(identity_css in links, f"{route} retains route-specific visual identity stylesheet {identity_css}")
    check("fonts.googleapis.com" not in text and "fonts.gstatic.com" not in text, f"{route} has no remote font-service link")

if failures:
    print(f"\nRESULT: FAIL ({len(failures)} issue(s))")
    return_code = 1
else:
    print("\nRESULT: PASS")
    return_code = 0

raise SystemExit(return_code)
