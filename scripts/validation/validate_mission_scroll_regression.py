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

EXPECTED_CASES = 8


class QuietHandler(
    SimpleHTTPRequestHandler
):

    def log_message(
        self,
        format,
        *args,
    ):
        pass


def browser_paths() -> dict[str, Path]:

    discovered: dict[
        str,
        Path
    ] = {}

    candidates: dict[
        str,
        list[Path]
    ] = {
        "edge": [],
        "chrome": [],
    }

    if os.name == "nt":

        env = os.environ

        possibilities = [
            (
                "PROGRAMFILES(X86)",
                (
                    "Microsoft/Edge/"
                    "Application/msedge.exe"
                ),
                "edge",
            ),
            (
                "PROGRAMFILES",
                (
                    "Microsoft/Edge/"
                    "Application/msedge.exe"
                ),
                "edge",
            ),
            (
                "LOCALAPPDATA",
                (
                    "Microsoft/Edge/"
                    "Application/msedge.exe"
                ),
                "edge",
            ),
            (
                "PROGRAMFILES",
                (
                    "Google/Chrome/"
                    "Application/chrome.exe"
                ),
                "chrome",
            ),
            (
                "PROGRAMFILES(X86)",
                (
                    "Google/Chrome/"
                    "Application/chrome.exe"
                ),
                "chrome",
            ),
            (
                "LOCALAPPDATA",
                (
                    "Google/Chrome/"
                    "Application/chrome.exe"
                ),
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

                discovered[
                    browser_name
                ] = path.resolve()

                break

    return discovered


def run_browser(
    browser_name: str,
    executable: Path,
    url: str,
) -> bool:

    with tempfile.TemporaryDirectory(
        prefix=(
            "a2-mission-r4-"
            +browser_name
            +"-"
        )
    ) as profile:

        command = [
            str(
                executable
            ),
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
            "--window-size=1700,1200",
            "--virtual-time-budget=70000",
            (
                "--user-data-dir="
                +profile
            ),
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
            timeout=95,
        )

        dom = (
            result.stdout
            or ""
        )


        def attribute(
            name: str,
        ) -> str:

            match = re.search(
                (
                    rf'{re.escape(name)}'
                    r'="([^"]+)"'
                ),
                dom,
                re.I,
            )

            return (
                match.group(1)
                if match
                else "MISSING"
            )


        status = attribute(
            "data-status"
        )

        case_count = attribute(
            "data-case-count"
        )

        scroll_delta = attribute(
            "data-max-scroll-delta"
        )

        shell_delta = attribute(
            "data-max-shell-height-delta"
        )

        stage_delta = attribute(
            "data-max-stage-height-delta"
        )

        controls_delta = attribute(
            "data-max-controls-top-delta"
        )

        width_delta = attribute(
            "data-max-client-width-delta"
        )

        control_overflow = attribute(
            "data-max-control-overflow"
        )


        result_match = re.search(
            (
                r'<pre id="results">'
                r'(.*?)'
                r'</pre>'
            ),
            dom,
            re.I | re.S,
        )

        detail_text = ""

        if result_match:

            detail_text = html.unescape(
                result_match.group(1)
            ).strip()


        print()
        print(
            f"[{browser_name.upper()}]"
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
            case_count,
        )

        print(
            "Max page-scroll delta:",
            scroll_delta,
            "px",
        )

        print(
            "Max shell-height delta:",
            shell_delta,
            "px",
        )

        print(
            "Max stage-height delta:",
            stage_delta,
            "px",
        )

        print(
            "Max controls-top delta:",
            controls_delta,
            "px",
        )

        print(
            "Max client-width delta:",
            width_delta,
            "px",
        )

        print(
            "Max control overflow:",
            control_overflow,
            "px",
        )


        passed = (
            status == "PASS"
            and case_count ==
            str(
                EXPECTED_CASES
            )
        )

        if not passed:

            if detail_text:

                try:

                    decoded = json.loads(
                        detail_text
                    )

                    print(
                        json.dumps(
                            decoded,
                            indent=2,
                        )
                    )

                except Exception:

                    print(
                        detail_text[
                            :26000
                        ]
                    )

            if result.stderr:

                print(
                    "Browser stderr:"
                )

                print(
                    result.stderr[
                        -5000:
                    ]
                )

            return False


        print(
            "PASS:",
            browser_name,
            (
                " Mission Explorer "
                "geometry + containment "
                "regression"
            ),
        )

        return True


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--required",
        action="store_true",
    )

    arguments = parser.parse_args()

    browsers = browser_paths()

    if not browsers:

        if arguments.required:

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
        arguments.required
        and os.name == "nt"
    ):

        missing = [
            browser_name
            for browser_name
            in (
                "edge",
                "chrome",
            )
            if browser_name
            not in browsers
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


    previous_cwd = Path.cwd()

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
        server.server_address[
            1
        ]
    )

    thread = threading.Thread(
        target=
          server.serve_forever,
        daemon=True,
    )

    thread.start()

    url = (
        f"http://127.0.0.1:{port}"
        "/scripts/validation/"
        "mission_scroll_regression.html"
    )

    outcomes: dict[
        str,
        bool
    ] = {}

    try:

        for browser_name in sorted(
            browsers
        ):

            outcomes[
                browser_name
            ] = run_browser(
                browser_name,
                browsers[
                    browser_name
                ],
                url,
            )

    finally:

        server.shutdown()

        server.server_close()

        os.chdir(
            previous_cwd
        )


    failures = [
        browser_name
        for (
            browser_name,
            passed,
        )
        in outcomes.items()
        if not passed
    ]


    if failures:

        print()

        print(
            "FAIL: Mission Explorer "
            "regression failed in:",
            ", ".join(
                failures
            ),
        )

        return 1


    print()
    print(
        "=" * 78
    )

    print(
        "MISSION EXPLORER GEOMETRY + "
        "CONTAINMENT REGRESSION PASSED"
    )

    print(
        "Browsers:",
        ", ".join(
            browser_name.upper()
            for browser_name
            in sorted(
                outcomes
            )
        ),
    )

    print(
        "Viewports per browser:",
        EXPECTED_CASES,
    )

    print(
        "Required drift: <= 1 px"
    )

    print(
        "Required control overflow: <= 1 px"
    )

    print(
        "=" * 78
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
