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


def find_browser() -> Path | None:
    candidates = []

    if os.name == "nt":
        env = os.environ

        for base_name, relative in [
            (
                "PROGRAMFILES(X86)",
                Path(
                    "Microsoft/Edge/Application/msedge.exe"
                ),
            ),
            (
                "PROGRAMFILES",
                Path(
                    "Microsoft/Edge/Application/msedge.exe"
                ),
            ),
            (
                "PROGRAMFILES",
                Path(
                    "Google/Chrome/Application/chrome.exe"
                ),
            ),
            (
                "PROGRAMFILES(X86)",
                Path(
                    "Google/Chrome/Application/chrome.exe"
                ),
            ),
            (
                "LOCALAPPDATA",
                Path(
                    "Google/Chrome/Application/chrome.exe"
                ),
            ),
            (
                "LOCALAPPDATA",
                Path(
                    "Microsoft/Edge/Application/msedge.exe"
                ),
            ),
        ]:
            base = env.get(base_name)

            if base:
                candidates.append(
                    Path(base) / relative
                )

    for command in [
        "microsoft-edge",
        "microsoft-edge-stable",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "chrome",
    ]:
        resolved = shutil.which(
            command
        )

        if resolved:
            candidates.append(
                Path(resolved)
            )

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the A2 MissionLab Windows "
            "gallery no-scroll browser regression."
        )
    )

    parser.add_argument(
        "--required",
        action="store_true",
        help=(
            "Fail if no compatible local "
            "Chromium-family browser is installed."
        ),
    )

    args = parser.parse_args()

    browser = find_browser()

    if browser is None:
        message = (
            "No local Microsoft Edge, Google Chrome, "
            "or Chromium executable was found."
        )

        if args.required:
            print(
                "FAIL:",
                message
            )
            return 1

        print(
            "SKIP:",
            message
        )
        return 0

    previous_cwd = Path.cwd()

    os.chdir(ROOT)

    server = ThreadingHTTPServer(
        (
            "127.0.0.1",
            0,
        ),
        QuietHandler,
    )

    port = server.server_address[1]

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    url = (
        "http://127.0.0.1:"
        f"{port}"
        "/scripts/validation/"
        "windows_scroll_regression.html"
    )

    try:
        with tempfile.TemporaryDirectory(
            prefix="a2-browser-"
        ) as temp_dir:

            command = [
                str(browser),
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
                "--window-size=1600,1200",
                "--virtual-time-budget=30000",
                f"--user-data-dir={temp_dir}",
                "--dump-dom",
                url,
            ]

            if os.name != "nt":
                command.insert(
                    1,
                    "--no-sandbox",
                )

            result = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=45,
            )

            dumped = (
                result.stdout
                or ""
            )

            status_match = re.search(
                r'data-status="([^"]+)"',
                dumped,
                re.I,
            )

            scroll_match = re.search(
                r'data-max-scroll-delta="([^"]+)"',
                dumped,
                re.I,
            )

            top_match = re.search(
                r'data-max-top-delta="([^"]+)"',
                dumped,
                re.I,
            )

            results_match = re.search(
                r'<pre id="results">(.*?)</pre>',
                dumped,
                re.I | re.S,
            )

            status = (
                status_match.group(1)
                if status_match
                else "MISSING"
            )

            scroll_delta = (
                scroll_match.group(1)
                if scroll_match
                else "?"
            )

            top_delta = (
                top_match.group(1)
                if top_match
                else "?"
            )

            details = ""

            if results_match:
                details = html.unescape(
                    results_match.group(1)
                ).strip()

            print(
                "Browser:",
                browser
            )

            print(
                "Regression status:",
                status
            )

            print(
                "Max scroll delta:",
                scroll_delta,
                "px"
            )

            print(
                "Max viewer-top delta:",
                top_delta,
                "px"
            )

            if details:
                print("")
                print(details)

            if status != "PASS":
                if result.stderr:
                    print("")
                    print(
                        "Browser stderr:"
                    )
                    print(
                        result.stderr[-4000:]
                    )

                return 1

            print("")
            print(
                "PASS: Windows gallery navigation "
                "preserved vertical page position."
            )

            return 0

    finally:
        server.shutdown()
        server.server_close()
        os.chdir(previous_cwd)


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
