from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "scripts" / "validation"

PORTABLE_SUITE = [
    ("Mission Explorer", "validate_mission_scroll_regression.py", ["--required"]),
    ("Through Orion Windows", "validate_windows_scroll_regression.py", ["--required"]),
    ("GNC", "validate_gnc_auto_regression.py", ["--required"]),
    ("Mission Control", "validate_mission_control_regression.py", ["--required"]),
    ("PSI", "validate_psi_regression.py", ["--required"]),
    ("Trajectory Correction", "validate_trajectory_regression.py", ["--required"]),
    ("Space Weather", "validate_space_weather_regression.py", ["--required"]),
    ("Entry / Descent / Recovery", "validate_entry_regression.py", ["--required"]),
    ("Global responsive", "validate_responsive_browser_qa.py", ["--required"]),
]

WINDOWS_ONLY_EXTENSION = [
    ("Phase K publication", "validate_phase_k_regression.py", ["--required"]),
    ("Phase L typography", "validate_phase_l_regression.py", ["--required"]),
    ("Phase M accessibility/responsive", "validate_phase_m_regression.py", []),
    ("Phase N performance/failure", "validate_phase_n_regression.py", ["--required"]),
    ("Phase O presentation", "validate_phase_o_regression.py", ["--required"]),
]


def run_gate(label: str, script_name: str, args: list[str], env: dict[str, str] | None = None) -> None:
    script = VALIDATION / script_name
    if not script.is_file():
        raise SystemExit(f"PHASE P BROWSER RELEASE GATE FAILED: missing {script_name}")
    print("\n" + "=" * 78)
    print("PHASE P GATE:", label)
    print("=" * 78)
    command = [sys.executable, str(script), *args]
    completed = subprocess.run(command, cwd=ROOT, check=False, env=env)
    if completed.returncode != 0:
        raise SystemExit(
            f"PHASE P BROWSER RELEASE GATE FAILED: {label} ({script_name}) returned {completed.returncode}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="A2 MissionLab Phase P release-candidate browser orchestration")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--portable", action="store_true", help="Required single-Chromium-family CI release smoke gate")
    mode.add_argument("--windows-release", action="store_true", help="Exhaustive local Windows Edge + Chrome release gate")
    args = parser.parse_args()

    if args.windows_release and os.name != "nt":
        print("FAIL: --windows-release is intentionally restricted to Windows.")
        return 1

    suite = list(PORTABLE_SUITE)
    if args.windows_release:
        suite.extend(WINDOWS_ONLY_EXTENSION)

    print("A2 MissionLab Phase P full release-candidate browser gate")
    print("=" * 78)
    print("Mode:", "WINDOWS EXHAUSTIVE" if args.windows_release else "PORTABLE CHROMIUM CI")
    print("Protected suites:", len(suite))
    print("Policy: first failure stops qualification; no browser skip is accepted")

    if args.portable and os.environ.get("PHASE_P_CHROME"):
        chrome = Path(os.environ["PHASE_P_CHROME"]).expanduser().resolve()
        if not chrome.is_file():
            print("FAIL: PHASE_P_CHROME does not resolve to a browser executable:", chrome)
            return 1
        with tempfile.TemporaryDirectory(prefix="a2-phase-p-chrome-") as shim_dir:
            shim = Path(shim_dir) / "google-chrome"
            shim.symlink_to(chrome)
            child_env = os.environ.copy()
            # Portable CI is intentionally a single pinned Chromium-family gate.
            # Isolate browser discovery to the shim so runner-installed browsers
            # cannot silently expand or destabilize portable qualification.
            child_env["PATH"] = str(Path(shim_dir))
            print("Portable Chrome:", chrome)
            for label, script, script_args in suite:
                run_gate(label, script, script_args, child_env)
    else:
        for label, script, script_args in suite:
            run_gate(label, script, script_args)

    print("\n" + "=" * 78)
    if args.windows_release:
        print("PHASE P WINDOWS EXHAUSTIVE BROWSER RELEASE GATE PASSED")
        print("Coverage: protected Edge + Chrome suites through completed Phase O")
    else:
        print("PHASE P PORTABLE CHROMIUM CI GATE PASSED")
        print("Coverage: mission interactions + simulations + global responsive smoke")
        print("Boundary: this is not Edge/Safari/real-device coverage")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
