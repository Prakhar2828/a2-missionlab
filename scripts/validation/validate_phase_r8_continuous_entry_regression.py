from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def browser_paths() -> dict[str, Path]:
    found: dict[str, Path] = {}
    candidates: dict[str, list[Path]] = {"edge": [], "chrome": []}
    if os.name == "nt":
        env = os.environ
        for key, rel, name in [
            ("PROGRAMFILES(X86)", "Microsoft/Edge/Application/msedge.exe", "edge"),
            ("PROGRAMFILES", "Microsoft/Edge/Application/msedge.exe", "edge"),
            ("LOCALAPPDATA", "Microsoft/Edge/Application/msedge.exe", "edge"),
            ("PROGRAMFILES", "Google/Chrome/Application/chrome.exe", "chrome"),
            ("PROGRAMFILES(X86)", "Google/Chrome/Application/chrome.exe", "chrome"),
            ("LOCALAPPDATA", "Google/Chrome/Application/chrome.exe", "chrome"),
        ]:
            base = env.get(key)
            if base:
                candidates[name].append(Path(base) / rel)
    else:
        for executable, name in [
            ("microsoft-edge", "edge"), ("microsoft-edge-stable", "edge"),
            ("google-chrome", "chrome"), ("google-chrome-stable", "chrome"),
            ("chromium", "chrome"), ("chromium-browser", "chrome"),
        ]:
            path = shutil.which(executable)
            if path:
                candidates[name].append(Path(path))
    for name, paths in candidates.items():
        for path in paths:
            if path.is_file():
                found[name] = path.resolve()
                break
    return found


def run_browser(name: str, executable: Path, url: str) -> bool:
    profile = Path(tempfile.mkdtemp(prefix=f"a2-r8-{name}-"))
    try:
        cmd = [
            str(executable), "--headless=new", "--disable-gpu", "--disable-dev-shm-usage",
            "--no-first-run", "--no-default-browser-check", "--disable-background-networking",
            "--disable-background-timer-throttling", "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding", "--run-all-compositor-stages-before-draw",
            "--disable-component-update", "--disable-sync", "--metrics-recording-only", "--mute-audio",
            "--window-size=1500,1100", "--virtual-time-budget=36000", f"--user-data-dir={profile}",
            "--dump-dom", url,
        ]
        if os.name != "nt":
            cmd.insert(1, "--no-sandbox")
        try:
            result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=52)
        except subprocess.TimeoutExpired:
            print(f"\n[{name.upper()}]\nFAIL: R8 continuous EDL regression timed out")
            return False

        dom = result.stdout or ""
        def attr(key: str) -> str:
            m = re.search(rf'{re.escape(key)}="([^"]+)"', dom, re.I)
            return m.group(1) if m else "MISSING"

        keys = [
            "data-status", "data-engineering-layout-pass", "data-engineering-play-pass",
            "data-continuity-pass", "data-context-pass", "data-splash-pass", "data-responsive-pass",
        ]
        vals = {k: attr(k) for k in keys}
        print(f"\n[{name.upper()}]")
        for k, v in vals.items():
            print(k.replace("data-", "").replace("-", " ") + ":", v)

        passed = vals["data-status"] == "PASS" and all(vals[k] == "true" for k in keys[1:])
        if not passed:
            m = re.search(r'<pre id="results">(.*?)</pre>', dom, re.I | re.S)
            if m:
                details = html.unescape(m.group(1)).strip()
                try:
                    print(json.dumps(json.loads(details), indent=2))
                except Exception:
                    print(details[:26000])
            if result.stderr:
                print("Browser stderr:\n" + result.stderr[-4000:])
            return False

        print("PASS:", name, "Phase R8 continuous EDL cinematic + viewport regression")
        return True
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--required", action="store_true")
    args = parser.parse_args()
    found = browser_paths()
    if not found:
        print("FAIL: no compatible browser found." if args.required else "SKIP: no compatible browser found.")
        return 1 if args.required else 0
    if args.required and os.name == "nt":
        missing = [name for name in ("edge", "chrome") if name not in found]
        if missing:
            print("FAIL: required Windows browser(s) missing:", ", ".join(missing))
            return 1

    old = Path.cwd()
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_address[1]}/scripts/validation/phase_r8_continuous_entry_regression.html"
    outcomes: dict[str, bool] = {}
    try:
        for name in sorted(found):
            outcomes[name] = run_browser(name, found[name], url)
    finally:
        server.shutdown()
        server.server_close()
        os.chdir(old)

    failures = [name for name, ok in outcomes.items() if not ok]
    if failures:
        print("\nFAIL: Phase R8 continuous EDL regression failed in:", ", ".join(failures))
        return 1

    print("\n" + "=" * 78)
    print("PHASE R8 CONTINUOUS EDL CINEMATIC + VIEWPORT REGRESSION PASSED")
    print("Browsers:", ", ".join(name.upper() for name in sorted(outcomes)))
    print("Verified: non-overlapping engineering graph chrome, in-stage playback, watchable cadence, continuous camera path, cloud-deck descent/drogues, late-ocean main descent, ocean-only splashdown, responsive containment")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
