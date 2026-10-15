from __future__ import annotations

import html
import json
import os
import re
import subprocess
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_CASES = 96


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def browser_paths() -> dict[str, Path]:
    env = os.environ
    candidates = {
        "edge": [
            (env.get("PROGRAMFILES(X86)"), "Microsoft/Edge/Application/msedge.exe"),
            (env.get("PROGRAMFILES"), "Microsoft/Edge/Application/msedge.exe"),
            (env.get("LOCALAPPDATA"), "Microsoft/Edge/Application/msedge.exe"),
        ],
        "chrome": [
            (env.get("PROGRAMFILES"), "Google/Chrome/Application/chrome.exe"),
            (env.get("PROGRAMFILES(X86)"), "Google/Chrome/Application/chrome.exe"),
            (env.get("LOCALAPPDATA"), "Google/Chrome/Application/chrome.exe"),
        ],
    }
    found: dict[str, Path] = {}
    for name, options in candidates.items():
        for base, relative in options:
            if not base:
                continue
            path = Path(base) / relative
            if path.is_file():
                found[name] = path.resolve()
                break
    return found


def run_browser(name: str, executable: Path, url: str) -> bool:
    with tempfile.TemporaryDirectory(prefix=f"a2-phase-m-{name}-") as profile:
        command = [
            str(executable),
            "--headless=new",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--run-all-compositor-stages-before-draw",
            "--disable-component-update",
            "--disable-sync",
            "--metrics-recording-only",
            "--mute-audio",
            "--hide-scrollbars",
            "--window-size=2000,1300",
            "--virtual-time-budget=100000",
            f"--user-data-dir={profile}",
            "--dump-dom",
            url,
        ]
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        dom = result.stdout or ""

        def attr(name: str) -> str:
            match = re.search(rf'{re.escape(name)}="([^"]+)"', dom, re.I)
            return match.group(1) if match else "MISSING"

        status = attr("data-status")
        cases = attr("data-case-count")
        failures = attr("data-failure-count")
        overflow = attr("data-max-overflow")
        print(f"\n[{name.upper()}]")
        print("Executable:", executable)
        print("Status:", status)
        print("Cases:", cases)
        print("Failures:", failures)
        print("Max horizontal overflow:", overflow, "px")

        if status != "PASS" or cases != str(EXPECTED_CASES) or failures != "0":
            match = re.search(r'<pre id="results">(.*?)</pre>', dom, re.I | re.S)
            if match:
                details = html.unescape(match.group(1)).strip()
                try:
                    parsed = json.loads(details)
                    print(json.dumps(parsed.get("failures", parsed), indent=2)[:16000])
                except Exception:
                    print(details[:16000])
            if result.stderr:
                print("Browser stderr:")
                print(result.stderr[-4000:])
            return False

        print("PASS:", name, "Phase M accessibility/responsive matrix")
        return True


def main() -> int:
    browsers = browser_paths()
    required = ["edge", "chrome"]
    missing = [name for name in required if name not in browsers]
    if missing:
        print("FAIL: missing browser(s):", ", ".join(missing))
        return 1

    old_cwd = Path.cwd()
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}/scripts/validation/phase_m_accessibility_regression.html"
    results: dict[str, bool] = {}
    try:
        for name in required:
            results[name] = run_browser(name, browsers[name], url)
    finally:
        server.shutdown()
        server.server_close()
        os.chdir(old_cwd)

    failed = [name for name, passed in results.items() if not passed]
    if failed:
        print("\nFAIL: Phase M browser QA failed in:", ", ".join(failed))
        return 1

    print("\n" + "=" * 76)
    print("PHASE M ACCESSIBILITY + RESPONSIVE BROWSER QA PASSED")
    print("Browsers: EDGE, CHROME")
    print("Routes: 8")
    print("Viewports per browser: 12")
    print("Cases per browser: 96")
    print("Total cases: 192")
    print("=" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
