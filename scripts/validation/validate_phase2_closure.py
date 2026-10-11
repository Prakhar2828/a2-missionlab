from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANIFEST_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_phase2_closure_manifest.json"
)

PHASE2K_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_phase2_integrated_operations.json"
)

GNC_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_gnc_operational_threads.json"
)

MANEUVER_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_operational_threads.json"
)

RUNNER_PATH = (
    ROOT
    / "scripts"
    / "run_phase2.py"
)


def fail(message):
    raise SystemExit(
        f"PHASE 2 CLOSURE VALIDATION FAILED: {message}"
    )


def load_json(path):
    if not path.exists():
        fail(
            f"missing file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


def require_file(path):
    if not path.exists():
        fail(
            f"missing required file: {path}"
        )


def main():
    manifest = load_json(
        MANIFEST_PATH
    )

    phase2k = load_json(
        PHASE2K_PATH
    )

    gnc = load_json(
        GNC_PATH
    )

    maneuvers = load_json(
        MANEUVER_PATH
    )

    #
    # Manifest identity
    #

    if (
        manifest.get("dataset_id")
        != "phase2_artemis_ii_full_closure_manifest"
    ):
        fail(
            "closure manifest dataset ID mismatch"
        )

    if (
        manifest.get("mission")
        != "Artemis II"
    ):
        fail(
            "mission identity mismatch"
        )

    if (
        manifest.get("phase")
        != "2"
    ):
        fail(
            "phase identity mismatch"
        )

    if (
        manifest.get("status")
        != "COMPLETE"
    ):
        fail(
            "Phase 2 manifest is not COMPLETE"
        )

    #
    # Reproducibility runner
    #

    require_file(
        RUNNER_PATH
    )

    runner_text = RUNNER_PATH.read_text(
        encoding="utf-8-sig"
    )

    required_runner_markers = [
        "PHASE 2 PIPELINE COMPLETE",
        "Phase 2A through Phase 2K",
        '"2A"',
        '"2B.1"',
        '"2B.2"',
        '"2C"',
        '"2D"',
        '"2E.1"',
        '"2E.2"',
        '"2E.3"',
        '"2E.4"',
        '"2F.1"',
        '"2F.2"',
        '"2F.3"',
        '"2F.4"',
        '"2G.1"',
        '"2G.2"',
        '"2H.1"',
        '"2H.2"',
        '"2H.3"',
        '"2H.4"',
        '"2I.1"',
        '"2I.2"',
        '"2I.3"',
        '"2I.4"',
        '"2J.1"',
        '"2J.2"',
        '"2J.3"',
        '"2J.4"',
        '"2K"',
    ]

    for marker in required_runner_markers:
        if marker not in runner_text:
            fail(
                "Phase 2 runner missing required "
                f"coverage marker: {marker}"
            )

    runner = manifest[
        "reproducibility_runner"
    ]

    if (
        runner["path"]
        != "scripts/run_phase2.py"
        or runner["expected_success_marker"]
        != "PHASE 2 PIPELINE COMPLETE"
        or runner["expected_coverage_start"]
        != "2A"
        or runner["expected_coverage_end"]
        != "2K"
        or runner["observed_successful_step_count"]
        != 58
        or runner["successful_run_required_for_closure"]
        is not True
    ):
        fail(
            "reproducibility-runner manifest mismatch"
        )

    #
    # Subphase closure
    #

    subphases = manifest[
        "subphases"
    ]

    expected_phase_ids = [
        "2A",
        "2B.1",
        "2B.2",
        "2C",
        "2D",
        "2E.1",
        "2E.2",
        "2E.3",
        "2E.4",
        "2F.1",
        "2F.2",
        "2F.3",
        "2F.4",
        "2G.1",
        "2G.2",
        "2H.1",
        "2H.2",
        "2H.3",
        "2H.4",
        "2I.1",
        "2I.2",
        "2I.3",
        "2I.4",
        "2J.1",
        "2J.2",
        "2J.3",
        "2J.4",
        "2K",
    ]

    observed_phase_ids = [
        item["phase_id"]
        for item in subphases
    ]

    if (
        observed_phase_ids
        != expected_phase_ids
    ):
        fail(
            "Phase 2 subphase set or order changed"
        )

    if (
        len(subphases)
        != 28
    ):
        fail(
            "expected 28 Phase 2 closure entries"
        )

    #
    # Every manifest validator must:
    #
    # 1. exist on disk;
    # 2. appear in the reproducibility runner.
    #
    # We test the script basename rather than the complete
    # path because run_phase2.py intentionally constructs
    # many paths from adjacent Python string literals.
    #

    for item in subphases:
        if (
            item["status"]
            != "COMPLETE"
        ):
            fail(
                "subphase not complete: "
                f"{item['phase_id']}"
            )

        validator_relative = Path(
            item[
                "validation_script"
            ]
        )

        validator = (
            ROOT
            / validator_relative
        )

        require_file(
            validator
        )

        validator_name = (
            validator_relative.name
        )

        if (
            validator_name
            not in runner_text
        ):
            fail(
                "Phase 2 runner does not invoke "
                f"validator for {item['phase_id']}: "
                f"{validator_name}"
            )

    #
    # Key tracked reference products
    #

    reference_products = (
        manifest[
            "key_reference_products"
        ]
    )

    if (
        len(reference_products)
        != len(
            set(
                reference_products
            )
        )
    ):
        fail(
            "duplicate reference product in manifest"
        )

    for relative_path in (
        reference_products
    ):
        require_file(
            ROOT
            / relative_path
        )

    #
    # Local reproducibility inputs
    #

    local_inputs = manifest[
        "key_local_reproducibility_inputs"
    ]

    if (
        len(local_inputs)
        != len(
            set(
                local_inputs
            )
        )
    ):
        fail(
            "duplicate local reproducibility input"
        )

    for relative_path in (
        local_inputs
    ):
        require_file(
            ROOT
            / relative_path
        )

    #
    # Phase 2K closure
    #

    if (
        phase2k.get("dataset_id")
        != "phase2k_artemis_ii_phase2_integrated_operations"
    ):
        fail(
            "Phase 2K dataset ID mismatch"
        )

    if (
        phase2k.get("phase2_status")
        != "COMPLETE"
    ):
        fail(
            "Phase 2K status is not COMPLETE"
        )

    #
    # Phase 2J closure
    #

    if (
        gnc.get("dataset_id")
        != "phase2j4_artemis_ii_gnc_operational_threads"
    ):
        fail(
            "Phase 2J.4 dataset ID mismatch"
        )

    closure = gnc[
        "phase2j_cross_phase_closure"
    ]

    expected_j_status = {
        "phase2j1": "COMPLETE",
        "phase2j2": "COMPLETE",
        "phase2j3": "COMPLETE",
        "phase2j4": "COMPLETE",
    }

    observed_j_status = {
        key: value["status"]
        for key, value in (
            closure.items()
        )
    }

    if (
        observed_j_status
        != expected_j_status
    ):
        fail(
            "Phase 2J closure mismatch"
        )

    #
    # Phase 2I closure
    #

    if (
        maneuvers.get("dataset_id")
        != "phase2i4_artemis_ii_maneuver_operational_threads"
    ):
        fail(
            "Phase 2I.4 dataset ID mismatch"
        )

    if (
    maneuvers[
        "phase_2i_closure_criteria"
    ][
        "phase_2i_ready_to_close"
    ]
    is not True
    ):
        fail(
            "Phase 2I is not ready to close"
        )

    #
    # Evidence-boundary policy
    #

    boundaries = manifest[
        "permanent_evidence_boundaries"
    ]

    required_boundaries = {
        "MODELED_ATMOSPHERIC_QUANTITIES_ARE_NOT_RAW_FLIGHT_TELEMETRY",
        "MODELED_CONVECTIVE_HEATING_IS_NOT_MEASURED_SURFACE_HEAT_FLUX",
        "EXPECTED_LUNAR_COMMUNICATIONS_BLACKOUT_IS_NOT_AN_ANOMALY",
        "CANCELLED_CORRECTION_IS_NOT_FAILED_BURN",
        "PUBLIC_OEM_IS_NOT_RAW_SPACECRAFT_TELEMETRY",
        "OEM_SOLUTION_DIFFERENCE_IS_NOT_NAVIGATION_ERROR",
        "OEM_SOLUTION_DIFFERENCE_IS_NOT_MEASURED_BURN_DELTA_V",
        "AROW_PUBLIC_STATE_VECTOR_IS_NOT_PROVEN_ORION_ONBOARD_FILTER_STATE",
        "DSN_GROUND_TRACKING_IS_NOT_AN_ONBOARD_NAVIGATION_SENSOR",
        "RTC3_TO_ENTRY_CLOCK_HANDOFF_IS_NOT_DETAILED_ENTRY_GUIDANCE_RECONSTRUCTION",
    }

    if not (
        required_boundaries
        .issubset(
            set(
                boundaries
            )
        )
    ):
        fail(
            "one or more permanent "
            "evidence boundaries missing"
        )

    #
    # Closure criteria
    #

    criteria = manifest[
        "closure_criteria"
    ]

    for key, value in (
        criteria.items()
    ):
        if (
            key
            == "unsupported_telemetry_fabricated"
        ):
            if value is not False:
                fail(
                    "unsupported telemetry "
                    "fabrication flag failed"
                )
        elif value is not True:
            fail(
                f"closure criterion failed: {key}"
            )

    #
    # Next phase handoff
    #

    if (
        manifest[
            "next_major_phase"
        ]
        != "3"
        or manifest[
            "next_major_phase_name"
        ]
        != (
            "ECLSS, Vehicle Systems, "
            "Thermal, and Materials"
        )
    ):
        fail(
            "next-major-phase handoff mismatch"
        )

    print(
        "A2 MissionLab Phase 2 Full Closure Validation"
    )

    print(
        "=" * 72
    )

    print()
    print("Closure manifest identity: PASS")
    print("Phase 2 status COMPLETE: PASS")
    print("Phase 2A through 2K coverage: PASS")
    print("28 subphase closure entries: PASS")
    print("All declared validators exist: PASS")
    print("All declared validators in runner: PASS")
    print("All key tracked reference products exist: PASS")
    print("All local reproducibility inputs exist: PASS")
    print("Phase 2K integration COMPLETE: PASS")
    print("Phase 2J closure COMPLETE: PASS")
    print("Phase 2I closure readiness: PASS")
    print("Evidence-boundary policy: PASS")
    print("Full reproducibility-run requirement: PASS")
    print("58-step successful-run record: PASS")
    print("Phase 3 handoff: PASS")

    print()

    print(
        "PHASE 2 FULL CLOSURE VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()