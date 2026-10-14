from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import tempfile
import threading

from http.server import (
    SimpleHTTPRequestHandler,
    ThreadingHTTPServer,
)

from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


class QuietHandler(
    SimpleHTTPRequestHandler
):
    def log_message(
        self,
        format,
        *args,
    ):
        pass


def browser_paths():

    env = os.environ

    candidates = {
        "edge": [
            (
                env.get(
                    "PROGRAMFILES(X86)"
                ),
                "Microsoft/Edge/Application/msedge.exe",
            ),
            (
                env.get(
                    "PROGRAMFILES"
                ),
                "Microsoft/Edge/Application/msedge.exe",
            ),
            (
                env.get(
                    "LOCALAPPDATA"
                ),
                "Microsoft/Edge/Application/msedge.exe",
            ),
        ],

        "chrome": [
            (
                env.get(
                    "PROGRAMFILES"
                ),
                "Google/Chrome/Application/chrome.exe",
            ),
            (
                env.get(
                    "PROGRAMFILES(X86)"
                ),
                "Google/Chrome/Application/chrome.exe",
            ),
            (
                env.get(
                    "LOCALAPPDATA"
                ),
                "Google/Chrome/Application/chrome.exe",
            ),
        ],
    }

    found = {}

    for name, options in candidates.items():

        for base, relative in options:

            if not base:
                continue

            path = (
                Path(base)
                / relative
            )

            if path.is_file():

                found[name] = (
                    path.resolve()
                )

                break

    return found


def run_browser(
    name,
    executable,
    url,
):

    with tempfile.TemporaryDirectory(
        prefix=f"a2-{name}-"
    ) as profile:

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
            "--window-size=1600,1200",
            "--virtual-time-budget=45000",
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
            timeout=75,
        )

        dom = (
            result.stdout
            or ""
        )

        def attr(name):

            match = re.search(
                rf'{re.escape(name)}="([^"]+)"',
                dom,
                re.I,
            )

            return (
                match.group(1)
                if match
                else "MISSING"
            )

        status = attr(
            "data-status"
        )

        cases = attr(
            "data-case-count"
        )

        failures = attr(
            "data-failure-count"
        )

        overflow = attr(
            "data-max-overflow"
        )

        result_match = re.search(
            r'<pre id="results">(.*?)</pre>',
            dom,
            re.I | re.S,
        )

        details = ""

        if result_match:

            details = html.unescape(
                result_match.group(1)
            ).strip()

        print("")
        print(
            f"[{name.upper()}]"
        )

        print(
            "Executable:",
            executable
        )

        print(
            "Status:",
            status
        )

        print(
            "Cases:",
            cases
        )

        print(
            "Failures:",
            failures
        )

        print(
            "Max horizontal overflow:",
            overflow,
            "px"
        )

        if status != "PASS":

            if details:

                try:

                    parsed = json.loads(
                        details
                    )

                    print("")

                    print(
                        json.dumps(
                            parsed.get(
                                "failures",
                                parsed
                            ),
                            indent=2
                        )
                    )

                except Exception:

                    print("")
                    print(
                        details[:12000]
                    )

            if result.stderr:

                print("")
                print(
                    "Browser stderr:"
                )

                print(
                    result.stderr[-3000:]
                )

            return False

        if cases != "42":

            print(
                "FAIL: expected 42 cases"
            )

            return False

        if failures != "0":

            print(
                "FAIL: expected zero failures"
            )

            return False

        print(
            "PASS:",
            name,
            "responsive matrix"
        )

        return True


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--required",
        action="store_true",
    )

    args = parser.parse_args()

    browsers = browser_paths()

    required_names = [
        "edge",
        "chrome",
    ]

    missing = [
        name
        for name
        in required_names
        if name not in browsers
    ]

    if missing:

        print(
            "FAIL: missing browser(s):",
            ", ".join(missing)
        )

        return 1

    old_cwd = Path.cwd()

    os.chdir(ROOT)

    server = ThreadingHTTPServer(
        (
            "127.0.0.1",
            0,
        ),
        QuietHandler,
    )

    port = (
        server.server_address[1]
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    url = (
        f"http://127.0.0.1:{port}"
        "/scripts/validation/"
        "responsive_browser_qa.html"
    )

    results = {}

    try:

        for name in required_names:

            results[name] = (
                run_browser(
                    name,
                    browsers[name],
                    url,
                )
            )

    finally:

        server.shutdown()
        server.server_close()

        os.chdir(old_cwd)

    failed = [
        name
        for name, passed
        in results.items()
        if not passed
    ]

    if failed:

        print("")
        print(
            "FAIL: responsive QA failed in:",
            ", ".join(failed)
        )

        return 1

    print("")
    print(
        "=" * 72
    )

    print(
        "RESPONSIVE BROWSER QA PASSED"
    )

    print(
        "Browsers: EDGE, CHROME"
    )

    print(
        "Routes: 7"
    )

    print(
        "Viewports per browser: 6"
    )

    print(
        "Cases per browser: 42"
    )

    print(
        "Total cases: 84"
    )

    print(
        "=" * 72
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
