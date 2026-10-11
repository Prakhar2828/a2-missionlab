from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable)


RAW_AROW_ARCHIVE = (
    ROOT
    / "data"
    / "raw"
    / "arow"
    / "all-artemis-ii-oem-files.zip"
)

EARTH_ORIENTATION_KERNEL = (
    ROOT
    / "data"
    / "raw"
    / "spice"
    / "earth_1962_260806_2126_combined.bpc"
)

PHASE1_SPICE_KERNELS = [
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

TRACKED_INPUTS = [
    ROOT
    / "data"
    / "config"
    / "mission.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_entry_events.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_msis_drivers.csv",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_msis_environment.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_rarefaction_model.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_convective_heating_model.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_tps_evidence.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_entry_profile_heritage.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_tps_physics_boundary.json",

    ROOT
    / "data"
    / "reference"
    / "dsn_topocentric_geometry_reference.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_event_catalog.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_events.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_o2o_reference.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_operational_threads.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_plan_execution.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_esm_propulsion_architecture.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_trajectory_correlation.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_operational_threads.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_gnc_architecture.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_manual_piloting_control_modes.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_navigation_state_estimation.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_gnc_operational_threads.json",

    ROOT
    / "data"
    / "reference"
    / "artemis_ii_phase2_integrated_operations.json",
]


def run_step(
    number: int,
    total: int,
    phase: str,
    label: str,
    script: str,
):
    script_path = ROOT / script

    if not script_path.exists():
        raise SystemExit(
            "\nPHASE 2 PIPELINE FAILED\n\n"
            "Required script does not exist:\n"
            f"{script_path}"
        )

    print()
    print("=" * 78)
    print(
        f"[{number}/{total}] "
        f"{phase} — {label}"
    )
    print("=" * 78)
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
        f"Completed in {elapsed:.2f} s"
    )


def preflight():
    print()
    print(
        "A2 MissionLab — "
        "Phase 2 Full Reproducibility Run"
    )
    print(
        "=" * 52
    )

    print()
    print(
        f"Repository: {ROOT}"
    )
    print(
        f"Python:     {PYTHON}"
    )

    required = [
        (
            "NASA AROW archive",
            RAW_AROW_ARCHIVE,
        ),
    ]

    required.extend(
        (
            f"Phase 1 SPICE kernel {path.name}",
            path,
        )
        for path in PHASE1_SPICE_KERNELS
    )

    required.extend(
        (
            f"Tracked input {path.name}",
            path,
        )
        for path in TRACKED_INPUTS
    )

    missing = []

    print()
    print("Preflight:")

    for label, path in required:
        exists = path.exists()

        status = (
            "OK"
            if exists
            else "MISSING"
        )

        print(
            f"  {status:7} {label}"
        )

        if not exists:
            missing.append(
                path
            )

    if missing:
        print()
        print(
            "PHASE 2 PREFLIGHT FAILED"
        )

        print()
        print(
            "Missing required inputs:"
        )

        for path in missing:
            print(
                f"  {path}"
            )

        print()
        print(
            "Phase 2 depends on the "
            "completed Phase 1 mission "
            "backbone and the local NASA "
            "AROW source archive."
        )

        raise SystemExit(1)


def earth_kernel_download_needed():
    if (
        EARTH_ORIENTATION_KERNEL.exists()
    ):
        print()
        print(
            "Pinned Earth-orientation kernel "
            "already present."
        )
        print(
            "Downloader will still validate "
            "the file when needed by the "
            "existing Phase 2 tooling."
        )

        return False

    print()
    print(
        "Pinned Earth-orientation kernel "
        "is missing."
    )
    print(
        "The verified NAIF downloader "
        "will run before Earth-fixed "
        "entry geometry."
    )

    return True


def main():
    preflight()

    needs_earth_kernel = (
        earth_kernel_download_needed()
    )

    steps = [
        #
        # Phase 2A
        #
        (
            "2A",
            "Parse high-rate entry trajectory",
            "scripts/ingestion/"
            "parse_entry_trajectory.py",
        ),
        (
            "2A",
            "Validate high-rate entry trajectory",
            "scripts/validation/"
            "validate_entry_trajectory.py",
        ),

        #
        # Phase 2B.1
        #
        (
            "2B.1",
            "Transform M50 analysis proxy to J2000",
            "scripts/processing/"
            "transform_entry_to_j2000.py",
        ),
        (
            "2B.1",
            "Validate entry frame transformation",
            "scripts/validation/"
            "validate_entry_frame_transform.py",
        ),
    ]

    if needs_earth_kernel:
        steps.append(
            (
                "2B.2",
                "Download and verify pinned "
                "Earth-orientation kernel",
                "scripts/ingestion/"
                "download_entry_earth_kernel.py",
            )
        )

    steps.extend(
        [
            #
            # Phase 2B.2
            #
            (
                "2B.2",
                "Build Earth-fixed and "
                "geodetic entry geometry",
                "scripts/processing/"
                "build_entry_geometry.py",
            ),
            (
                "2B.2",
                "Validate Earth-fixed and "
                "geodetic entry geometry",
                "scripts/validation/"
                "validate_entry_geometry.py",
            ),

            #
            # Phase 2C
            #
            (
                "2C",
                "Analyze entry dynamics",
                "scripts/analysis/"
                "analyze_entry_dynamics.py",
            ),
            (
                "2C",
                "Validate entry dynamics",
                "scripts/validation/"
                "validate_entry_dynamics.py",
            ),

            #
            # Phase 2D
            #
            (
                "2D",
                "Correlate entry and "
                "recovery events",
                "scripts/analysis/"
                "correlate_entry_events.py",
            ),
            (
                "2D",
                "Validate entry and "
                "recovery events",
                "scripts/validation/"
                "validate_entry_events.py",
            ),

            #
            # Phase 2E.1
            #
            (
                "2E.1",
                "Build modeled entry atmosphere "
                "and dynamic pressure",
                "scripts/analysis/"
                "build_entry_atmosphere.py",
            ),
            (
                "2E.1",
                "Validate entry atmosphere",
                "scripts/validation/"
                "validate_entry_atmosphere.py",
            ),

            #
            # Phase 2E.2
            #
            (
                "2E.2",
                "Build free-stream Mach "
                "and flow-regime reconstruction",
                "scripts/analysis/"
                "build_entry_mach.py",
            ),
            (
                "2E.2",
                "Validate Mach reconstruction",
                "scripts/validation/"
                "validate_entry_mach.py",
            ),

            #
            # Phase 2E.3
            #
            (
                "2E.3",
                "Build body-scale rarefaction "
                "and continuum analysis",
                "scripts/analysis/"
                "build_entry_rarefaction.py",
            ),
            (
                "2E.3",
                "Validate rarefaction analysis",
                "scripts/validation/"
                "validate_entry_rarefaction.py",
            ),

            #
            # Phase 2E.4
            #
            (
                "2E.4",
                "Build Sutton-Graves "
                "convective-heating reconstruction",
                "scripts/analysis/"
                "build_entry_heating.py",
            ),
            (
                "2E.4",
                "Validate convective-heating "
                "reconstruction",
                "scripts/validation/"
                "validate_entry_heating.py",
            ),

            #
            # Phase 2F.1
            #
            (
                "2F.1",
                "Validate Orion TPS evidence",
                "scripts/validation/"
                "validate_tps_evidence.py",
            ),
            (
                "2F.1",
                "Build TPS engineering "
                "decision thread",
                "scripts/analysis/"
                "build_tps_decision_thread.py",
            ),
            (
                "2F.1",
                "Validate TPS decision thread",
                "scripts/validation/"
                "validate_tps_decision_thread.py",
            ),

            #
            # Phase 2F.2
            #
            (
                "2F.2",
                "Validate entry-profile "
                "heritage evidence",
                "scripts/validation/"
                "validate_entry_profile_heritage.py",
            ),
            (
                "2F.2",
                "Compare Artemis entry profiles",
                "scripts/analysis/"
                "compare_artemis_entry_profiles.py",
            ),
            (
                "2F.2",
                "Validate Artemis entry-profile "
                "comparison",
                "scripts/validation/"
                "validate_artemis_entry_profile_comparison.py",
            ),

            #
            # Phase 2F.3
            #
            (
                "2F.3",
                "Analyze loft / rebound "
                "heating history",
                "scripts/analysis/"
                "analyze_loft_heating_history.py",
            ),
            (
                "2F.3",
                "Validate loft / rebound "
                "heating history",
                "scripts/validation/"
                "validate_loft_heating_history.py",
            ),

            #
            # Phase 2F.4
            #
            (
                "2F.4",
                "Build TPS evidence-to-physics "
                "boundary",
                "scripts/analysis/"
                "build_tps_physics_boundary.py",
            ),
            (
                "2F.4",
                "Validate TPS evidence-to-physics "
                "boundary",
                "scripts/validation/"
                "validate_tps_physics_boundary.py",
            ),

            #
            # Phase 2G.1
            #
            (
                "2G.1",
                "Build geocentric lunar "
                "occultation geometry",
                "scripts/analysis/"
                "build_lunar_occultation_geometry.py",
            ),
            (
                "2G.1",
                "Validate lunar-occultation "
                "geometry",
                "scripts/validation/"
                "validate_lunar_occultation_geometry.py",
            ),

            #
            # Phase 2G.2
            #
            (
                "2G.2",
                "Build topocentric DSN geometry",
                "scripts/analysis/"
                "build_dsn_topocentric_geometry.py",
            ),
            (
                "2G.2",
                "Validate topocentric DSN geometry",
                "scripts/validation/"
                "validate_dsn_topocentric_geometry.py",
            ),

            #
            # Phase 2H.1
            #
            (
                "2H.1",
                "Build communications "
                "event timeline",
                "scripts/analysis/"
                "build_communications_event_timeline.py",
            ),
            (
                "2H.1",
                "Validate communications "
                "event timeline",
                "scripts/validation/"
                "validate_communications_event_timeline.py",
            ),

            #
            # Phase 2H.2
            #
            (
                "2H.2",
                "Build mission-clock "
                "communications correlation",
                "scripts/analysis/"
                "build_mission_clock_communications_correlation.py",
            ),
            (
                "2H.2",
                "Validate mission-clock "
                "communications correlation",
                "scripts/validation/"
                "validate_mission_clock_communications_correlation.py",
            ),

            #
            # Phase 2H.3
            #
            (
                "2H.3",
                "Analyze O2O optical "
                "communications",
                "scripts/analysis/"
                "analyze_o2o_optical_communications.py",
            ),
            (
                "2H.3",
                "Validate O2O optical "
                "communications",
                "scripts/validation/"
                "validate_o2o_optical_communications.py",
            ),

            #
            # Phase 2H.4
            #
            (
                "2H.4",
                "Analyze communications "
                "operational threads",
                "scripts/analysis/"
                "analyze_communications_operational_threads.py",
            ),
            (
                "2H.4",
                "Validate communications "
                "operational threads",
                "scripts/validation/"
                "validate_communications_operational_threads.py",
            ),

            #
            # Phase 2I.1
            #
            (
                "2I.1",
                "Analyze maneuver plan "
                "versus execution",
                "scripts/analysis/"
                "analyze_maneuver_plan_execution.py",
            ),
            (
                "2I.1",
                "Validate maneuver plan "
                "versus execution",
                "scripts/validation/"
                "validate_maneuver_plan_execution.py",
            ),

            #
            # Phase 2I.2
            #
            (
                "2I.2",
                "Analyze ESM propulsion "
                "architecture",
                "scripts/analysis/"
                "analyze_esm_propulsion_architecture.py",
            ),
            (
                "2I.2",
                "Validate ESM propulsion "
                "architecture",
                "scripts/validation/"
                "validate_esm_propulsion_architecture.py",
            ),

            #
            # Phase 2I.3
            #
            (
                "2I.3",
                "Analyze maneuver trajectory "
                "correlation",
                "scripts/analysis/"
                "analyze_maneuver_trajectory_correlation.py",
            ),
            (
                "2I.3",
                "Validate maneuver trajectory "
                "correlation",
                "scripts/validation/"
                "validate_maneuver_trajectory_correlation.py",
            ),

            #
            # Phase 2I.4
            #
            (
                "2I.4",
                "Analyze maneuver "
                "operational threads",
                "scripts/analysis/"
                "analyze_maneuver_operational_threads.py",
            ),
            (
                "2I.4",
                "Validate maneuver "
                "operational threads",
                "scripts/validation/"
                "validate_maneuver_operational_threads.py",
            ),

            #
            # Phase 2J.1
            #
            (
                "2J.1",
                "Analyze GNC architecture",
                "scripts/analysis/"
                "analyze_gnc_architecture.py",
            ),
            (
                "2J.1",
                "Validate GNC architecture",
                "scripts/validation/"
                "validate_gnc_architecture.py",
            ),

            #
            # Phase 2J.2
            #
            (
                "2J.2",
                "Analyze manual piloting "
                "and control modes",
                "scripts/analysis/"
                "analyze_manual_piloting_control_modes.py",
            ),
            (
                "2J.2",
                "Validate manual piloting "
                "and control modes",
                "scripts/validation/"
                "validate_manual_piloting_control_modes.py",
            ),

            #
            # Phase 2J.3
            #
            (
                "2J.3",
                "Analyze navigation and "
                "state estimation evidence",
                "scripts/analysis/"
                "analyze_navigation_state_estimation.py",
            ),
            (
                "2J.3",
                "Validate navigation and "
                "state estimation evidence",
                "scripts/validation/"
                "validate_navigation_state_estimation.py",
            ),

            #
            # Phase 2J.4
            #
            (
                "2J.4",
                "Analyze GNC operational threads",
                "scripts/analysis/"
                "analyze_gnc_operational_threads.py",
            ),
            (
                "2J.4",
                "Validate GNC operational threads",
                "scripts/validation/"
                "validate_gnc_operational_threads.py",
            ),

            #
            # Phase 2K
            #
            (
                "2K",
                "Analyze integrated "
                "Phase 2 operations",
                "scripts/analysis/"
                "analyze_phase2_integrated_operations.py",
            ),
            (
                "2K",
                "Validate integrated "
                "Phase 2 operations",
                "scripts/validation/"
                "validate_phase2_integrated_operations.py",
            ),
        ]
    )

    #
    # Verify the complete pipeline before
    # executing any stage.
    #
    missing_scripts = []

    for _, _, script in steps:
        path = ROOT / script

        if not path.exists():
            missing_scripts.append(
                path
            )

    if missing_scripts:
        print()
        print(
            "PHASE 2 PIPELINE DEFINITION FAILED"
        )

        print()
        print(
            "Missing scripts:"
        )

        for path in missing_scripts:
            print(
                f"  {path}"
            )

        raise SystemExit(1)

    print()
    print(
        f"Pipeline steps: {len(steps)}"
    )

    pipeline_start = (
        time.perf_counter()
    )

    for number, (
        phase,
        label,
        script,
    ) in enumerate(
        steps,
        start=1,
    ):
        run_step(
            number,
            len(steps),
            phase,
            label,
            script,
        )

    elapsed = (
        time.perf_counter()
        - pipeline_start
    )

    print()
    print("=" * 78)
    print(
        "PHASE 2 PIPELINE COMPLETE"
    )
    print("=" * 78)

    print()
    print(
        f"Completed {len(steps)} "
        f"steps in {elapsed:.2f} seconds."
    )

    print()
    print(
        "Phase 2A through Phase 2K "
        "regenerated and validated "
        "successfully."
    )

    print()
    print(
        "Coverage:"
    )

    print(
        "  Phase 2A   "
        "High-rate entry trajectory"
    )
    print(
        "  Phase 2B   "
        "Frame transformation and "
        "Earth-fixed geometry"
    )
    print(
        "  Phase 2C   "
        "Entry dynamics"
    )
    print(
        "  Phase 2D   "
        "Entry / recovery events"
    )
    print(
        "  Phase 2E   "
        "Atmosphere, Mach, rarefaction, "
        "and heating"
    )
    print(
        "  Phase 2F   "
        "TPS evidence, heritage, and "
        "heating-history analysis"
    )
    print(
        "  Phase 2G   "
        "Lunar occultation and DSN geometry"
    )
    print(
        "  Phase 2H   "
        "Communications"
    )
    print(
        "  Phase 2I   "
        "Maneuvers and propulsion"
    )
    print(
        "  Phase 2J   "
        "Guidance, navigation, and control"
    )
    print(
        "  Phase 2K   "
        "Cross-domain integration"
    )

    print()
    print(
        "This runner verifies technical "
        "reproducibility. Git closure is "
        "a separate repository-state check."
    )


if __name__ == "__main__":
    main()