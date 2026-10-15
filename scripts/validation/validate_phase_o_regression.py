from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_CASES = 96


class QuietHandler(SimpleHTTPRequestHandler):
    result_token = ""
    result_event = None
    result_payload = None

    def log_message(self, format, *args):
        pass

    def do_POST(self):
        split = urlsplit(self.path)
        if split.path != "/__phase_o_result__":
            self.send_error(404)
            return
        token = parse_qs(split.query).get("token", [""])[0]
        if token != type(self).result_token:
            self.send_error(403, "Phase O result token mismatch")
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
            self.send_error(400, f"Invalid Phase O result payload: {exc}")


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


def run_browser(label: str, executable: Path, url: str, handler_type: type[QuietHandler]) -> bool:
    with tempfile.TemporaryDirectory(prefix=f"a2-phase-o-{label}-") as profile:
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
            process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=stderr_file)
            completed = False
            try:
                completed = bool(handler_type.result_event and handler_type.result_event.wait(timeout=90))
            finally:
                if process.poll() is None:
                    if os.name == "nt":
                        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=12)
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
        failures = payload.get("failures", []) if isinstance(payload, dict) else [{"label": "browser completion handshake timeout", "detail": "No Phase O result POST received within 90 seconds."}]
        print(f"\n[{label.upper()}]")
        print("Executable:", executable)
        print("Status:", status)
        print("Cases:", cases)
        print("Failures:", len(failures) if isinstance(failures, list) else "INVALID")

        passed = status == "PASS" and cases == str(EXPECTED_CASES) and isinstance(failures, list) and len(failures) == 0
        if not passed:
            try:
                print(json.dumps({"cases": int(cases), "failures": failures}, indent=2)[:20000])
            except Exception:
                print(str(payload)[:20000])
            if stderr:
                print("Browser stderr:")
                print(stderr[-5000:])
            return False
        print("PASS:", label, "Phase O metadata/social presentation regression")
        return True


def serve_and_run(label: str, executable: Path) -> bool:
    token = os.urandom(18).hex()
    event = threading.Event()
    handler = type("PhaseOHandler", (QuietHandler,), {"result_token": token, "result_event": event, "result_payload": None})
    old_cwd = Path.cwd()
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}/scripts/validation/phase_o_presentation_regression.html?token={token}"
    try:
        return run_browser(label, executable, url, handler)
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

    results = {label: serve_and_run(label, executable) for label, executable in targets.items()}
    failed = [name for name, passed in results.items() if not passed]
    if failed:
        print("\nFAIL: Phase O browser QA failed in:", ", ".join(failed))
        return 1

    print("\n" + "=" * 78)
    print("PHASE O README + SOCIAL METADATA BROWSER QA PASSED")
    if args.browser:
        print("Package-build browser:", args.label.upper(), "(not the Windows release gate)")
    else:
        print("Windows release browsers: EDGE, CHROME")
    print("Routes: 8")
    print(f"Cases per browser: {EXPECTED_CASES}")
    print(f"Total cases: {EXPECTED_CASES * len(targets)}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
