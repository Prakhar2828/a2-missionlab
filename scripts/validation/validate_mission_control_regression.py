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
        prefix=f"a2-mc-{name}-"
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
            "--window-size=1700,1300",
            "--virtual-time-budget=65000",
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
            timeout=95,
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

        layout_delta = attr(
            "data-max-layout-delta"
        )

        scroll_delta = attr(
            "data-max-scroll-delta"
        )

        min_touch = attr(
            "data-min-touch-target"
        )

        context_overflow = attr(
            "data-max-context-overflow"
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
            executable,
        )

        print(
            "Status:",
            status,
        )

        print(
            "Viewport cases:",
            cases,
        )

        print(
            "Failures:",
            failures,
        )

        print(
            "Max horizontal overflow:",
            overflow,
            "px",
        )

        print(
            "Max layout delta:",
            layout_delta,
            "px",
        )

        print(
            "Max page-scroll delta:",
            scroll_delta,
            "px",
        )

        print(
            "Max fixed-context content overflow:",
            context_overflow,
            "px",
        )

        print(
            "Minimum scenario/role touch target:",
            min_touch,
            "px",
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
                            parsed,
                            indent=2,
                        )[:20000]
                    )

                except Exception:

                    print("")
                    print(
                        details[:20000]
                    )

            if result.stderr:

                print("")
                print(
                    "Browser stderr:"
                )

                print(
                    result.stderr[-4000:]
                )

            return False

        if cases != "6":

            print(
                "FAIL: expected 6 viewport cases"
            )

            return False

        if failures != "0":

            print(
                "FAIL: expected zero failures"
            )

            return False

        try:

            if float(overflow) > 1:

                print(
                    "FAIL: horizontal overflow exceeded 1 px"
                )

                return False

            if float(layout_delta) > 1:

                print(
                    "FAIL: layout delta exceeded 1 px"
                )

                return False

            if float(scroll_delta) > 1:

                print(
                    "FAIL: page-scroll delta exceeded 1 px"
                )

                return False

            if float(context_overflow) > 1:

                print(
                    "FAIL: fixed context panel clipped content"
                )

                return False

            if float(min_touch) < 64:

                print(
                    "FAIL: touch target fell below 64 px"
                )

                return False

        except ValueError:

            print(
                "FAIL: regression metrics were not numeric"
            )

            return False

        print(
            "PASS:",
            name,
            "Mission Control Phase D regression",
        )

        return True


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Run the A2 MissionLab Phase D "
            "Mission Control browser regression."
        )
    )

    parser.add_argument(
        "--required",
        action="store_true",
        help=(
            "Fail if Microsoft Edge or "
            "Google Chrome is unavailable."
        ),
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

        message = (
            "missing browser(s): "
            + ", ".join(
                missing
            )
        )

        if args.required:

            print(
                "FAIL:",
                message,
            )

            return 1

        print(
            "SKIP:",
            message,
        )

        return 0

    old_cwd = Path.cwd()

    os.chdir(
        ROOT
    )

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
        "mission_control_regression.html"
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

        os.chdir(
            old_cwd
        )

    failed = [
        name
        for name, passed
        in results.items()
        if not passed
    ]

    if failed:

        print("")

        print(
            "FAIL: Mission Control regression failed in:",
            ", ".join(
                failed
            ),
        )

        return 1

    print("")
    print(
        "=" * 72
    )

    print(
        "PHASE D MISSION CONTROL REGRESSION PASSED"
    )

    print(
        "Browsers: EDGE, CHROME"
    )

    print(
        "Viewports per browser: 6"
    )

    print(
        "Scenario/lens combinations per viewport: 28"
    )

    print(
        "Interactions per browser: 168"
    )

    print(
        "Total scenario/lens interactions: 336"
    )

    print(
        "Decision model stages: 7"
    )

    print(
        "Narrative/canvas intersection: 0"
    )

    print(
        "Required touch target: >= 64 px"
    )

    print(
        "Allowed layout/page-scroll delta: <= 1 px"
    )

    print(
        "Allowed fixed-context clipping: <= 1 px"
    )

    print(
        "=" * 72
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
