from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable)

RAW_OEM_ARCHIVE = (
    ROOT
    / "data"
    / "raw"
    / "arow"
    / "all-artemis-ii-oem-files.zip"
)

MISSION_CONFIG = (
    ROOT
    / "data"
    / "config"
    / "mission.json"
)

EVENT_CATALOG = (
    ROOT
    / "data"
    / "reference"
    / "trajectory_events.json"
)

SPICE_KERNELS = [
    ROOT
    / "data"
    / "raw"
    / "spice"
    / "de440s.bsp",

    ROOT
    / "data"
    / "raw"
    / "spice"
    / "naif0012.tls",

    ROOT
    / "data"
    / "raw"
    / "spice"
    / "pck00011.tpc",
]


def run_step(
    number: int,
    total: int,
    label: str,
    script: str,
):
    script_path = (
        ROOT / script
    )

    if not script_path.exists():
        raise SystemExit(
            "\nERROR: Required script "
            "does not exist:\n"
            f"{script_path}"
        )

    print()
    print("=" * 72)
    print(
        f"[{number}/{total}] "
        f"{label}"
    )
    print("=" * 72)
    print(
        f"{PYTHON} {script_path}"
    )
    print()

    start = time.perf_counter()

    subprocess.run(
        [
            str(PYTHON),
            str(script_path),
        ],
        cwd=ROOT,
        check=True,
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print()
    print(
        f"Completed in "
        f"{elapsed:.2f} s"
    )


def preflight():
    print()
    print(
        "A2 MissionLab — "
        "Phase 1 Reproducibility Run"
    )
    print(
        "=========================================="
    )

    print()
    print(
        f"Repository: {ROOT}"
    )

    print(
        f"Python:     {PYTHON}"
    )

    required_files = [
        (
            "NASA AROW OEM archive",
            RAW_OEM_ARCHIVE,
        ),
        (
            "Mission configuration",
            MISSION_CONFIG,
        ),
        (
            "Trajectory event catalog",
            EVENT_CATALOG,
        ),
    ]

    missing = []

    print()
    print("Preflight:")

    for label, path in required_files:
        exists = path.exists()

        status = (
            "OK"
            if exists
            else "MISSING"
        )

        print(
            f"  {status:7} "
            f"{label}"
        )

        if not exists:
            missing.append(
                path
            )

    if missing:
        print()
        print(
            "PHASE 1 PREFLIGHT FAILED"
        )

        print()
        print(
            "Missing required files:"
        )

        for path in missing:
            print(
                f"  {path}"
            )

        print()
        print(
            "The raw NASA OEM archive "
            "is intentionally not stored "
            "in Git."
        )

        raise SystemExit(1)


def spice_download_needed():
    missing = [
        path
        for path in SPICE_KERNELS
        if not path.exists()
    ]

    if not missing:
        print()
        print(
            "SPICE kernels already present. "
            "Skipping download."
        )

        return False

    print()
    print(
        "One or more SPICE kernels "
        "are missing:"
    )

    for path in missing:
        print(
            f"  {path.name}"
        )

    print()
    print(
        "The SPICE kernel downloader "
        "will run."
    )

    return True


def main():
    preflight()

    needs_spice = (
        spice_download_needed()
    )

    steps = [
        (
            "Validate Phase 0 foundation data",
            "scripts/validate_data.py",
        ),
        (
            "Parse NASA Artemis II OEM products",
            "scripts/ingestion/parse_oem.py",
        ),
        (
            "Validate parsed trajectory products",
            "scripts/validation/validate_trajectory.py",
        ),
        (
            "Build primary April 10 trajectory",
            "scripts/processing/build_primary_trajectory.py",
        ),
    ]

    if needs_spice:
        steps.append(
            (
                "Download required JPL/NAIF "
                "SPICE kernels",
                "scripts/ingestion/"
                "download_spice_kernels.py",
            )
        )

    steps.extend(
        [
            (
                "Add JPL SPICE lunar geometry",
                "scripts/processing/"
                "add_lunar_geometry.py",
            ),
            (
                "Refine lunar closest approach",
                "scripts/analysis/"
                "refine_lunar_closest_approach.py",
            ),
            (
                "Classify geometric mission phases",
                "scripts/analysis/"
                "classify_mission_phases.py",
            ),
            (
                "Compare public NASA OEM products",
                "scripts/analysis/"
                "compare_oem_products.py",
            ),
            (
                "Analyze time-resolved OEM evolution",
                "scripts/analysis/"
                "analyze_oem_evolution.py",
            ),
            (
                "Overlay documented trajectory events",
                "scripts/analysis/"
                "overlay_trajectory_events.py",
            ),
            (
                "Analyze trajectory event windows",
                "scripts/analysis/"
                "analyze_event_windows.py",
            ),
            (
                "Decompose OEM residuals into RTN",
                "scripts/analysis/"
                "analyze_rtn_residuals.py",
            ),
            (
                "Validate RTN residual decomposition",
                "scripts/validation/"
                "validate_rtn_residuals.py",
            ),
        ]
    )

    print()
    print(
        f"Pipeline steps: "
        f"{len(steps)}"
    )

    pipeline_start = (
        time.perf_counter()
    )

    for number, (
        label,
        script,
    ) in enumerate(
        steps,
        start=1,
    ):
        run_step(
            number,
            len(steps),
            label,
            script,
        )

    elapsed = (
        time.perf_counter()
        - pipeline_start
    )

    print()
    print("=" * 72)
    print(
        "PHASE 1 PIPELINE COMPLETE"
    )
    print("=" * 72)

    print()
    print(
        f"Completed "
        f"{len(steps)} steps "
        f"in {elapsed:.2f} seconds."
    )

    print()
    print(
        "Mission backbone regenerated "
        "and validated successfully."
    )

    print()
    print("NOTE:")

    print(
        "The separate high-rate "
        "Post-RTC3-to-Entry-Interface "
        "trajectory remains intentionally "
        "outside Phase 1 and is reserved "
        "for dedicated entry analysis."
    )


if __name__ == "__main__":
    main()