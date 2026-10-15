from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_CASES = 20


class QuietHandler(SimpleHTTPRequestHandler):
    fail_celestial = False
    result_token = ""
    result_event = None
    result_payload = None

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        path = urlsplit(self.path).path
        if self.fail_celestial and path in {
            "/assets/public/celestial/earth_pia18033.jpg",
            "/assets/public/celestial/moon_lro_mosaic.jpg",
        }:
            self.send_error(404, "Phase N intentional celestial failure")
            return
        super().do_GET()

    def do_POST(self):
        split = urlsplit(self.path)
        if split.path != "/__phase_n_result__":
            self.send_error(404)
            return
        token = parse_qs(split.query).get("token", [""])[0]
        if token != type(self).result_token:
            self.send_error(403, "Phase N result token mismatch")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 65536:
                raise ValueError("invalid result payload size")
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("result payload is not an object")
            type(self).result_payload = payload
            event = type(self).result_event
            if event is not None:
                event.set()
            self.send_response(204)
            self.end_headers()
        except Exception as exc:
            self.send_error(400, f"Invalid Phase N result payload: {exc}")


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


def run_browser(label: str, executable: Path, url: str, mode: str, handler_type: type[QuietHandler]) -> bool:
    with tempfile.TemporaryDirectory(prefix=f"a2-phase-n-{label}-{mode}-") as profile:
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
            "--window-size=1500,1000",
            f"--user-data-dir={profile}",
            url,
        ]
        if os.name != "nt":
            command.insert(2, "--no-sandbox")

        with tempfile.TemporaryFile(mode="w+b") as stderr_file:
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=stderr_file,
            )
            completed = False
            try:
                completed = bool(handler_type.result_event and handler_type.result_event.wait(timeout=90))
            finally:
                if process.poll() is None:
                    if os.name == "nt":
                        subprocess.run(
                            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=False,
                            timeout=12,
                        )
                    else:
                        process.terminate()
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=8)
                stderr_file.seek(0)
                stderr = stderr_file.read().decode("utf-8", errors="replace")

        payload = handler_type.result_payload if completed else None
        status = str(payload.get("status", "TIMEOUT")) if isinstance(payload, dict) else "TIMEOUT"
        cases = str(payload.get("cases", 0)) if isinstance(payload, dict) else "0"
        failures = payload.get("failures", []) if isinstance(payload, dict) else [
            {"label": "browser completion handshake timeout", "detail": "No Phase N result POST received within 90 seconds."}
        ]

        print(f"\n[{label.upper()} · {mode.upper()}]")
        print("Executable:", executable)
        print("Status:", status)
        print("Cases:", cases)
        print("Failures:", len(failures) if isinstance(failures, list) else "INVALID")

        passed = (
            status == "PASS"
            and cases == str(EXPECTED_CASES)
            and isinstance(failures, list)
            and len(failures) == 0
        )
        if not passed:
            try:
                print(json.dumps({"mode": mode, "cases": int(cases), "failures": failures}, indent=2)[:20000])
            except Exception:
                print(str(payload)[:20000])
            if stderr:
                print("Browser stderr:")
                print(stderr[-5000:])
            return False

        print("PASS:", label, mode, "Phase N regression")
        return True


def serve_and_run(label: str, executable: Path, failure_mode: bool) -> bool:
    token = os.urandom(18).hex()
    event = threading.Event()
    handler = type(
        "PhaseNHandler",
        (QuietHandler,),
        {
            "fail_celestial": failure_mode,
            "result_token": token,
            "result_event": event,
            "result_payload": None,
        },
    )
    old_cwd = Path.cwd()
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    mode = "failure" if failure_mode else "normal"
    url = (
        f"http://127.0.0.1:{port}/scripts/validation/phase_n_performance_regression.html"
        f"?failure={1 if failure_mode else 0}&token={token}"
    )
    try:
        return run_browser(label, executable, url, mode, handler)
    finally:
        server.shutdown()
        server.server_close()
        os.chdir(old_cwd)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--required", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--browser", help="Run one explicit Chromium-family executable (package-build convenience only).")
    parser.add_argument("--label", default="chromium")
    args = parser.parse_args()

    if args.browser:
        executable = Path(args.browser).resolve()
        if not executable.is_file():
            print("FAIL: browser executable not found:", executable)
            return 1
        targets = {args.label: executable}
    else:
        targets = browser_paths()
        missing = [name for name in ("edge", "chrome") if name not in targets]
        if missing:
            print("FAIL: missing browser(s):", ", ".join(missing))
            return 1
        targets = {name: targets[name] for name in ("edge", "chrome")}

    results: dict[str, bool] = {}
    for label, executable in targets.items():
        results[f"{label}-normal"] = serve_and_run(label, executable, False)
        results[f"{label}-failure"] = serve_and_run(label, executable, True)

    failed = [name for name, passed in results.items() if not passed]
    if failed:
        print("\nFAIL: Phase N browser QA failed in:", ", ".join(failed))
        return 1

    print("\n" + "=" * 82)
    print("PHASE N PERFORMANCE + FAILURE-STATE BROWSER QA PASSED")
    if args.browser:
        print("Package-build browser:", args.label.upper(), "(not the Windows release gate)")
    else:
        print("Windows release browsers: EDGE, CHROME")
    print("Modes per browser: normal assets + intentional celestial 404 failure")
    print(f"Cases per mode: {EXPECTED_CASES}")
    print(f"Cases per browser: {EXPECTED_CASES * 2}")
    print(f"Total cases: {EXPECTED_CASES * 2 * len(targets)}")
    print("=" * 82)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
