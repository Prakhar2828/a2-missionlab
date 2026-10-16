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

    found = {}

    candidates = {
        "edge": [],
        "chrome": [],
    }

    if os.name == "nt":

        env = os.environ

        possibilities = [
            (
                "PROGRAMFILES(X86)",
                "Microsoft/Edge/Application/msedge.exe",
                "edge",
            ),
            (
                "PROGRAMFILES",
                "Microsoft/Edge/Application/msedge.exe",
                "edge",
            ),
            (
                "LOCALAPPDATA",
                "Microsoft/Edge/Application/msedge.exe",
                "edge",
            ),
            (
                "PROGRAMFILES",
                "Google/Chrome/Application/chrome.exe",
                "chrome",
            ),
            (
                "PROGRAMFILES(X86)",
                "Google/Chrome/Application/chrome.exe",
                "chrome",
            ),
            (
                "LOCALAPPDATA",
                "Google/Chrome/Application/chrome.exe",
                "chrome",
            ),
        ]

        for (
            environment_name,
            relative_path,
            browser_name,
        ) in possibilities:

            base = env.get(
                environment_name
            )

            if base:

                candidates[
                    browser_name
                ].append(
                    Path(base)
                    / relative_path
                )

    else:

        possibilities = [
            (
                "microsoft-edge",
                "edge",
            ),
            (
                "microsoft-edge-stable",
                "edge",
            ),
            (
                "google-chrome",
                "chrome",
            ),
            (
                "google-chrome-stable",
                "chrome",
            ),
            (
                "chromium",
                "chrome",
            ),
            (
                "chromium-browser",
                "chrome",
            ),
        ]

        for (
            executable_name,
            browser_name,
        ) in possibilities:

            executable = shutil.which(
                executable_name
            )

            if executable:

                candidates[
                    browser_name
                ].append(
                    Path(
                        executable
                    )
                )

    for (
        browser_name,
        paths,
    ) in candidates.items():

        for path in paths:

            if path.is_file():

                found[
                    browser_name
                ] = path.resolve()

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

        if cases != "48":

            print(
                "FAIL: expected 48 cases"
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

    if not browsers:

        if args.required:

            print(
                "FAIL: no compatible "
                "Chromium-family browser found."
            )

            return 1

        print(
            "SKIP: no compatible "
            "Chromium-family browser found."
        )

        return 0

    if (
        args.required
        and os.name == "nt"
    ):

        missing = [
            name
            for name
            in (
                "edge",
                "chrome",
            )
            if name not in browsers
        ]

        if missing:

            print(
                "FAIL: required Windows "
                "browser(s) missing:",
                ", ".join(
                    missing
                ),
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

        for name in sorted(browsers):

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
        "Browsers:",
        ", ".join(
            name.upper()
            for name in sorted(
                results
            )
        ),
    )

    print(
        "Routes: 8"
    )

    print(
        "Viewports per browser: 6"
    )

    print(
        "Cases per browser: 48"
    )

    print(
        "Total cases:",
        48 * len(
            results
        ),
    )

    print(
        "=" * 72
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
