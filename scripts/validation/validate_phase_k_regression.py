from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def browser_paths() -> dict[str, Path]:
    env = os.environ
    options = {
        "edge": [(env.get("PROGRAMFILES(X86)"), "Microsoft/Edge/Application/msedge.exe"), (env.get("PROGRAMFILES"), "Microsoft/Edge/Application/msedge.exe"), (env.get("LOCALAPPDATA"), "Microsoft/Edge/Application/msedge.exe")],
        "chrome": [(env.get("PROGRAMFILES"), "Google/Chrome/Application/chrome.exe"), (env.get("PROGRAMFILES(X86)"), "Google/Chrome/Application/chrome.exe"), (env.get("LOCALAPPDATA"), "Google/Chrome/Application/chrome.exe")],
    }
    found: dict[str, Path] = {}
    if os.name == "nt":
        for name, candidates in options.items():
            for base, rel in candidates:
                if base and (Path(base) / rel).is_file():
                    found[name] = (Path(base) / rel).resolve()
                    break
    else:
        for name, commands in {"chrome": ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"], "edge": ["microsoft-edge", "microsoft-edge-stable"]}.items():
            for command in commands:
                path = shutil.which(command)
                if path:
                    found[name] = Path(path).resolve()
                    break
    return found


def run_browser(name: str, executable: Path, url: str) -> bool:
    with tempfile.TemporaryDirectory(prefix=f"a2-phase-k-{name}-") as profile:
        command = [str(executable), "--headless=new", "--disable-gpu", "--disable-dev-shm-usage", "--no-first-run", "--no-default-browser-check", "--disable-background-networking", "--disable-background-timer-throttling", "--disable-backgrounding-occluded-windows", "--disable-renderer-backgrounding", "--run-all-compositor-stages-before-draw", "--disable-component-update", "--disable-sync", "--metrics-recording-only", "--mute-audio", "--hide-scrollbars", "--window-size=1600,1200", "--virtual-time-budget=45000", f"--user-data-dir={profile}", "--dump-dom", url]
        if os.name != "nt":
            command.insert(1, "--no-sandbox")
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=75)
        dom = result.stdout or ""
        def attr(key: str) -> str:
            m = re.search(rf'{re.escape(key)}="([^"]+)"', dom, re.I)
            return m.group(1) if m else "MISSING"
        details_match = re.search(r'<pre id="results">(.*?)</pre>', dom, re.I | re.S)
        details = html.unescape(details_match.group(1)).strip() if details_match else ""
        status = attr("data-status")
        print(f"\n[{name.upper()}]")
        print("Executable:", executable)
        print("Status:", status)
        print("Cases:", attr("data-case-count"))
        print("Failures:", attr("data-failure-count"))
        print("Max horizontal overflow:", attr("data-max-overflow"), "px")
        print("Initial library cards:", attr("data-library-cards"))
        print("Focused library article count:", attr("data-library-article-count"))
        print("Report figures:", attr("data-report-figures"))
        print("Report tables:", attr("data-report-tables"))
        if status != "PASS" and details:
            print(details)
        if result.returncode != 0 and status != "PASS":
            print("Browser exit code:", result.returncode)
            if result.stderr.strip():
                print(result.stderr.strip()[-1200:])
        return status == "PASS"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase K Mission Library + Technical Report browser regression.")
    parser.add_argument("--required", action="store_true")
    args = parser.parse_args()
    browsers = browser_paths()
    if not browsers:
        msg = "No local Chrome, Edge, or Chromium-family browser found."
        print(("FAIL: " if args.required else "SKIP: ") + msg)
        return 1 if args.required else 0
    if args.required and os.name == "nt" and not {"chrome", "edge"}.issubset(browsers):
        print("FAIL: Phase K release requires both Chrome and Edge on Windows.")
        return 1

    previous = Path.cwd(); os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler); thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    url = f"http://127.0.0.1:{server.server_address[1]}/scripts/validation/phase_k_publication_regression.html"
    try:
        passed = [run_browser(name, exe, url) for name, exe in browsers.items()]
    finally:
        server.shutdown(); server.server_close(); os.chdir(previous)
    if not all(passed):
        print("\nPHASE K PUBLICATION REGRESSION FAILED")
        return 1
    print("\n" + "=" * 72)
    print("PHASE K MISSION LIBRARY + TECHNICAL REPORT REGRESSION PASSED")
    print("Verified: categorized question discovery, focused deep-dive rendering, stable evidence links, report publication apparatus, responsive containment")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
