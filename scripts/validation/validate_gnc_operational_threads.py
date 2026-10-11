from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = ROOT / "data" / "reference" / "artemis_ii_gnc_operational_threads.json"
GNC_PATH = ROOT / "data" / "reference" / "artemis_ii_gnc_architecture.json"
MANUAL_PATH = ROOT / "data" / "reference" / "artemis_ii_manual_piloting_control_modes.json"
NAV_PATH = ROOT / "data" / "reference" / "artemis_ii_navigation_state_estimation.json"
MANEUVER_PATH = ROOT / "data" / "reference" / "artemis_ii_maneuver_operational_threads.json"

THREAD_CSV = ROOT / "data" / "processed" / "gnc" / "gnc_operational_threads.csv"
CLOSURE_CSV = ROOT / "data" / "processed" / "gnc" / "phase2j_closure_matrix.csv"
SUMMARY_PATH = ROOT / "data" / "processed" / "gnc" / "gnc_operational_threads_summary.json"

THREAD_FIGURE = ROOT / "docs" / "assets" / "gnc" / "phase2j4_gnc_operational_threads.svg"
CLOSURE_FIGURE = ROOT / "docs" / "assets" / "gnc" / "phase2j4_phase2j_closure.svg"


def fail(message):
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def load_json(path):
    if not path.exists():
        fail(f"missing file: {path}")

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


def load_csv(path):
    if not path.exists():
        fail(f"missing file: {path}")

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        return list(
            csv.DictReader(f)
        )


def validate_svg(path):
    if not path.exists():
        fail(f"missing SVG: {path}")

    if path.stat().st_size < 1000:
        fail(f"SVG unexpectedly small: {path}")

    if "<svg" not in path.read_text(
        encoding="utf-8"
    ):
        fail(f"invalid SVG content: {path}")


def main():
    reference = load_json(REFERENCE_PATH)
    gnc = load_json(GNC_PATH)
    manual = load_json(MANUAL_PATH)
    navigation = load_json(NAV_PATH)
    maneuvers = load_json(MANEUVER_PATH)
    summary = load_json(SUMMARY_PATH)

    thread_rows = load_csv(THREAD_CSV)
    closure_rows = load_csv(CLOSURE_CSV)

    expected_ids = {
        REFERENCE_PATH:
            "phase2j4_artemis_ii_gnc_operational_threads",

        GNC_PATH:
            "phase2j1_artemis_ii_gnc_architecture",

        MANUAL_PATH:
            "phase2j2_artemis_ii_manual_piloting_control_modes",

        NAV_PATH:
            "phase2j3_artemis_ii_navigation_state_estimation",

        MANEUVER_PATH:
            "phase2i4_artemis_ii_maneuver_operational_threads",
    }

    loaded = {
        REFERENCE_PATH: reference,
        GNC_PATH: gnc,
        MANUAL_PATH: manual,
        NAV_PATH: navigation,
        MANEUVER_PATH: maneuvers,
    }

    for path, expected in expected_ids.items():
        if loaded[path].get(
            "dataset_id"
        ) != expected:
            fail(
                f"dataset ID mismatch: {path.name}"
            )

    expected_thread_ids = [
        "proximity_operations_gnc",
        "flight_day_4_manual_piloting",
        "deep_space_navigation",
        "trajectory_correction_gnc",
        "final_correction_to_entry_handoff",
    ]

    threads = reference[
        "operational_threads"
    ]

    if [
        item["thread_id"]
        for item in threads
    ] != expected_thread_ids:
        fail(
            "operational thread identities changed"
        )

    if len(
        thread_rows
    ) != 5:
        fail(
            "operational thread CSV row count mismatch"
        )

    if [
        row["thread_id"]
        for row in thread_rows
    ] != expected_thread_ids:
        fail(
            "operational thread CSV identity mismatch"
        )

    expected_sensor_ids = [
        "star_tracker",
        "imu",
        "gps_receiver",
        "barometric_altimeter",
        "optical_navigation_camera",
        "sun_sensor",
    ]

    if (
        reference[
            "core_architecture"
        ][
            "onboard_navigation_sensor_ids"
        ]
        != expected_sensor_ids
        or reference[
            "core_architecture"
        ][
            "onboard_navigation_sensor_count"
        ]
        != 6
    ):
        fail(
            "Phase 2J.4 navigation architecture mismatch"
        )

    if [
        item["sensor_id"]
        for item in (
            gnc[
                "onboard_navigation_architecture"
            ][
                "sensors"
            ]
        )
    ] != expected_sensor_ids:
        fail(
            "Phase 2J.1 navigation architecture mismatch"
        )

    expected_statement = (
        "ONBOARD_NAVIGATION_STATE != "
        "GROUND_ORBIT_DETERMINATION != "
        "AROW_PUBLIC_STATE_VECTOR"
    )

    if (
        reference[
            "state_product_boundary"
        ][
            "statement"
        ]
        != expected_statement
        or navigation[
            "critical_state_product_boundary"
        ][
            "statement"
        ]
        != expected_statement
    ):
        fail(
            "state-product boundary mismatch"
        )

    if (
        reference[
            "state_product_boundary"
        ][
            "arow_equals_onboard_filter_state_proven"
        ]
        is not False
        or reference[
            "state_product_boundary"
        ][
            "arow_equals_complete_ground_navigation_solution_proven"
        ]
        is not False
    ):
        fail(
            "unsupported AROW equivalence introduced"
        )

    manual_core = (
        reference[
            "core_architecture"
        ][
            "manual_control"
        ]
    )

    if (
        manual_core[
            "rotational_hand_controller_domain"
        ]
        != "ATTITUDE"
        or manual_core[
            "translational_hand_controller_domain"
        ]
        != "TRANSLATION"
        or manual_core[
            "hand_controller_is_direct_thruster_switch"
        ]
        is not False
        or manual_core[
            "command_path"
        ]
        != [
            "CREW_CONTROLLER_INPUT",
            "GNC_FLIGHT_SOFTWARE",
            "EFFECTOR_SELECTION",
            "RCS_THRUSTER_COMMAND",
        ]
    ):
        fail(
            "manual-control architecture mismatch"
        )

    if (
        manual[
            "manual_control_architecture"
        ][
            "command_path"
        ]
        != manual_core[
            "command_path"
        ]
    ):
        fail(
            "Phase 2J.2 manual-control dependency mismatch"
        )

    proximity = threads[0]

    if (
        proximity[
            "execution_status"
        ]
        != "COMPLETED"
        or proximity[
            "duration_minutes"
        ]
        != 70.0
        or proximity[
            "evidence_boundaries"
        ][
            "all_17_premission_steps_confirmed_as_flown"
        ]
        is not False
    ):
        fail(
            "proximity thread mismatch"
        )

    if (
        manual[
            "proximity_operations"
        ][
            "as_flown"
        ][
            "onboard_navigation_sensors_used"
        ]
        is not True
        or manual[
            "proximity_operations"
        ][
            "as_flown"
        ][
            "reaction_control_thrusters_used"
        ]
        is not True
        or manual[
            "proximity_operations"
        ][
            "as_flown"
        ][
            "automated_departure_confirmed"
        ]
        is not True
    ):
        fail(
            "Phase 2J.2 proximity dependency mismatch"
        )

    fd4 = threads[1]

    if (
        fd4[
            "derived_start_utc"
        ]
        != "2026-04-05T01:09:00Z"
        or fd4[
            "derived_start_met"
        ]
        != "03:02:33:48"
        or fd4[
            "duration_minutes"
        ]
        != 41
        or fd4[
            "derived_end_utc"
        ]
        != "2026-04-05T01:50:00Z"
        or fd4[
            "derived_end_met"
        ]
        != "03:03:14:48"
    ):
        fail(
            "Flight Day 4 clock mismatch"
        )

    deep = threads[2]

    if (
        deep[
            "critical_boundary"
        ]
        != expected_statement
        or deep[
            "evidence_boundaries"
        ][
            "complete_onboard_filter_state_history_public"
        ]
        is not False
        or deep[
            "evidence_boundaries"
        ][
            "complete_ground_orbit_determination_solution_history_public"
        ]
        is not False
    ):
        fail(
            "deep-space navigation boundary mismatch"
        )

    nav_evidence = (
        navigation[
            "artemis_ii_as_flown_navigation_evidence"
        ]
    )

    if (
        nav_evidence[
            "optical_navigation_imagery"
        ][
            "earth_images_captured"
        ]
        is not True
        or nav_evidence[
            "optical_navigation_imagery"
        ][
            "moon_images_captured"
        ]
        is not True
        or nav_evidence[
            "proximity_operations_navigation"
        ][
            "onboard_navigation_sensors_used"
        ]
        is not True
    ):
        fail(
            "Phase 2J.3 as-flown navigation evidence mismatch"
        )

    correction = threads[3]

    if (
        correction[
            "public_oem_context"
        ][
            "maneuver_brackets_audited"
        ]
        != 4
        or correction[
            "public_oem_context"
        ][
            "same_epoch_solution_comparisons_available"
        ]
        != 3
        or correction[
            "public_oem_context"
        ][
            "same_epoch_comparisons_are_navigation_error"
        ]
        is not False
        or correction[
            "public_oem_context"
        ][
            "same_epoch_comparisons_are_measured_burn_delta_v"
        ]
        is not False
        or correction[
            "public_oem_context"
        ][
            "creation_time_proves_maneuver_assimilation"
        ]
        is not False
    ):
        fail(
            "trajectory-correction OEM boundary mismatch"
        )

    correction_steps = {
        item["step_id"]: item
        for item in correction[
            "operational_sequence"
        ]
    }

    if (
        correction_steps[
            "otc3_execution"
        ][
            "duration_seconds"
        ]
        != 17.5
        or correction_steps[
            "rtc1_execution"
        ][
            "reported_delta_v_ft_s"
        ]
        != 1.6
        or correction_steps[
            "rtc2_execution"
        ][
            "reported_delta_v_ft_s"
        ]
        != 5.3
        or correction_steps[
            "rtc3_execution"
        ][
            "reported_delta_v_ft_s"
        ]
        != 4.2
    ):
        fail(
            "trajectory-correction values mismatch"
        )

    if (
        reference[
            "core_architecture"
        ][
            "correction_burn_engine_assignments_resolved"
        ]
        != 0
        or reference[
            "core_architecture"
        ][
            "correction_burn_engine_assignments_unresolved"
        ]
        != 4
        or maneuvers[
            "propulsion_boundary"
        ][
            "correction_burn_engine_assignments_resolved"
        ]
        != 0
        or maneuvers[
            "propulsion_boundary"
        ][
            "correction_burn_engine_assignments_unresolved"
        ]
        != 4
    ):
        fail(
            "correction-burn propulsion boundary mismatch"
        )

    final_thread = threads[4]

    final_steps = {
        item[
            "step_id"
        ]:
            item
        for item in final_thread[
            "operational_sequence"
        ]
    }

    if (
        final_steps[
            "rtc3"
        ][
            "timestamp_utc"
        ]
        != "2026-04-10T18:53:00Z"
        or final_steps[
            "rtc3_to_entry_interval"
        ][
            "interval_seconds"
        ]
        != 18000.0
        or final_steps[
            "entry_interface"
        ][
            "timestamp_utc"
        ]
        != "2026-04-10T23:53:00Z"
    ):
        fail(
            "final correction-to-entry handoff mismatch"
        )

    for key, value in (
        final_thread[
            "phase2j_boundary"
        ].items()
    ):
        if (
            key
            == "final_correction_to_entry_clock_relationship_established"
        ):
            if value is not True:
                fail(
                    "final entry handoff relationship missing"
                )
        elif value is not False:
            fail(
                f"unsupported entry detail introduced: {key}"
            )

    closure = reference[
        "phase2j_cross_phase_closure"
    ]

    if list(
        closure
    ) != [
        "phase2j1",
        "phase2j2",
        "phase2j3",
        "phase2j4",
    ]:
        fail(
            "closure matrix identity mismatch"
        )

    expected_closure_status = [
        "COMPLETE",
        "COMPLETE",
        "COMPLETE",
        "COMPLETE",
    ]

    if [
        item[
            "status"
        ]
        for item in closure.values()
    ] != expected_closure_status:
        fail(
            "closure matrix status mismatch"
        )

    if len(
        closure_rows
    ) != 4:
        fail(
            "closure CSV row count mismatch"
        )

    if [
        row[
            "phase_id"
        ]
        for row in closure_rows
    ] != list(
        closure
    ):
        fail(
            "closure CSV phase identity mismatch"
        )

    if [
        row[
            "status"
        ]
        for row in closure_rows
    ] != expected_closure_status:
        fail(
            "closure CSV status mismatch"
        )

    criteria = reference[
        "closure_criteria"
    ]

    for key, value in criteria.items():
        if (
            key
            == "unsupported_telemetry_fabricated"
        ):
            if value is not False:
                fail(
                    "unsupported telemetry fabrication flag failed"
                )
        elif value is not True:
            fail(
                f"closure criterion failed: {key}"
            )

    if (
        "DETAILED_AS_FLOWN_ENTRY_GUIDANCE_WHERE_PUBLIC_EVIDENCE_SUPPORTS_IT"
        not in reference[
            "deferred_scope"
        ][
            "phase4_entry_descent_splashdown_recovery"
        ]
        or "DECISION_THREADS"
        not in reference[
            "deferred_scope"
        ][
            "phase7_mission_control_engineering_perspectives"
        ]
    ):
        fail(
            "deferred-scope boundary mismatch"
        )

    if (
        summary[
            "product_id"
        ]
        != "phase2j4_gnc_operational_threads_analysis"
    ):
        fail(
            "summary product ID mismatch"
        )

    if (
        summary[
            "operational_thread_count"
        ]
        != 5
    ):
        fail(
            "summary thread count mismatch"
        )

    if (
        summary[
            "operational_thread_ids"
        ]
        != expected_thread_ids
    ):
        fail(
            "summary thread identities mismatch"
        )

    if (
        summary[
            "anomaly_thread_count"
        ]
        != 0
    ):
        fail(
            "unexpected anomaly thread count"
        )

    if (
        summary[
            "correction_burn_engine_assignments_resolved"
        ]
        != 0
        or summary[
            "correction_burn_engine_assignments_unresolved"
        ]
        != 4
    ):
        fail(
            "summary propulsion boundary mismatch"
        )

    expected_generated = [
        "data/processed/gnc/gnc_operational_threads.csv",
        "data/processed/gnc/phase2j_closure_matrix.csv",
        "data/processed/gnc/gnc_operational_threads_summary.json",
        "docs/assets/gnc/phase2j4_gnc_operational_threads.svg",
        "docs/assets/gnc/phase2j4_phase2j_closure.svg",
    ]

    if (
        summary[
            "generated_products"
        ]
        != expected_generated
    ):
        fail(
            "generated-product manifest mismatch"
        )

    validate_svg(
        THREAD_FIGURE
    )

    validate_svg(
        CLOSURE_FIGURE
    )

    print(
        "Phase 2J.4 GNC Operational Threads & Closure Validation"
    )

    print(
        "=" * 72
    )

    print()
    print("Reference dataset: PASS")
    print("2J.1 architecture integration: PASS")
    print("2J.2 manual/proximity integration: PASS")
    print("2J.3 navigation integration: PASS")
    print("2I.4 maneuver integration: PASS")
    print("Five GNC operational threads: PASS")
    print("State-product boundary: PASS")
    print("Correction-engine uncertainty: PASS")
    print("OEM non-inference boundary: PASS")
    print("Final correction-to-entry boundary: PASS")
    print("Phase 4 / Phase 7 deferred scope: PASS")
    print("Processed products: PASS")
    print("Documentation figures: PASS")
    print()
    print("PHASE 2J.4 VALIDATION PASSED")


if __name__ == "__main__":
    main()
