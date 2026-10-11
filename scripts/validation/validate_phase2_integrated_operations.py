from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_phase2_integrated_operations.json"
)

FLIGHT_DYNAMICS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_trajectory_correlation.json"
)

COMMUNICATIONS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_operational_threads.json"
)

PROPULSION_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_esm_propulsion_architecture.json"
)

MANEUVERS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_operational_threads.json"
)

GNC_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_gnc_operational_threads.json"
)

OUTPUT_DIR = ROOT / "data" / "processed" / "phase2"

THREAD_CSV = (
    OUTPUT_DIR
    / "phase2_integrated_operational_threads.csv"
)

DOMAIN_CSV = (
    OUTPUT_DIR
    / "phase2_domain_closure.csv"
)

SUMMARY_PATH = (
    OUTPUT_DIR
    / "phase2_integrated_operations_summary.json"
)

THREAD_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "phase2"
    / "phase2k_integrated_operational_threads.svg"
)

DOMAIN_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "phase2"
    / "phase2k_domain_closure.svg"
)


def fail(message):
    raise SystemExit(
        f"VALIDATION FAILED: {message}"
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


def load_csv(path):
    if not path.exists():
        fail(
            f"missing file: {path}"
        )

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
        fail(
            f"missing SVG: {path}"
        )

    if (
        path.stat().st_size
        < 1000
    ):
        fail(
            f"SVG unexpectedly small: {path}"
        )

    text = path.read_text(
        encoding="utf-8"
    )

    if "<svg" not in text:
        fail(
            f"invalid SVG: {path}"
        )


def get_thread(items, thread_id):
    for item in items:
        if (
            item[
                "thread_id"
            ]
            == thread_id
        ):
            return item

    fail(
        f"missing thread: {thread_id}"
    )


def get_step(thread, step_id):
    for item in (
        thread[
            "operational_sequence"
        ]
    ):
        if (
            item[
                "step_id"
            ]
            == step_id
        ):
            return item

    fail(
        f"missing step: {step_id}"
    )


def main():
    reference = load_json(
        REFERENCE_PATH
    )

    flight_dynamics = load_json(
        FLIGHT_DYNAMICS_PATH
    )

    communications = load_json(
        COMMUNICATIONS_PATH
    )

    propulsion = load_json(
        PROPULSION_PATH
    )

    maneuvers = load_json(
        MANEUVERS_PATH
    )

    gnc = load_json(
        GNC_PATH
    )

    summary = load_json(
        SUMMARY_PATH
    )

    thread_rows = load_csv(
        THREAD_CSV
    )

    domain_rows = load_csv(
        DOMAIN_CSV
    )

    #
    # Dataset identities
    #

    expected_ids = {
        REFERENCE_PATH:
            "phase2k_artemis_ii_phase2_integrated_operations",

        FLIGHT_DYNAMICS_PATH:
            "phase2i3_artemis_ii_maneuver_trajectory_correlation",

        COMMUNICATIONS_PATH:
            "phase2h4_artemis_ii_communications_operational_threads",

        PROPULSION_PATH:
            "phase2i2_artemis_ii_esm_propulsion_architecture",

        MANEUVERS_PATH:
            "phase2i4_artemis_ii_maneuver_operational_threads",

        GNC_PATH:
            "phase2j4_artemis_ii_gnc_operational_threads",
    }

    loaded = {
        REFERENCE_PATH:
            reference,

        FLIGHT_DYNAMICS_PATH:
            flight_dynamics,

        COMMUNICATIONS_PATH:
            communications,

        PROPULSION_PATH:
            propulsion,

        MANEUVERS_PATH:
            maneuvers,

        GNC_PATH:
            gnc,
    }

    for path, expected in (
        expected_ids.items()
    ):
        if (
            loaded[path].get(
                "dataset_id"
            )
            != expected
        ):
            fail(
                f"dataset ID mismatch: {path.name}"
            )

    if (
        reference[
            "phase"
        ]
        != "2K"
    ):
        fail(
            "phase identifier mismatch"
        )

    if (
        reference[
            "phase2_status"
        ]
        not in {
            "IMPLEMENTATION_IN_PROGRESS",
            "COMPLETE",
        }
    ):
        fail(
            "invalid Phase 2 status"
        )

    #
    # Domain closure
    #

    expected_domains = [
        "flight_dynamics",
        "communications",
        "propulsion",
        "maneuvers",
        "gnc",
    ]

    if (
        list(
            reference[
                "phase2_domain_status"
            ]
        )
        != expected_domains
    ):
        fail(
            "domain identity mismatch"
        )

    for domain in expected_domains:
        if (
            reference[
                "phase2_domain_status"
            ][domain][
                "status"
            ]
            != "COMPLETE_TO_PHASE2_SCOPE"
        ):
            fail(
                f"domain not closed: {domain}"
            )

    if (
        len(
            domain_rows
        )
        != 5
    ):
        fail(
            "domain CSV row count mismatch"
        )

    if (
        [
            row[
                "domain"
            ]
            for row in domain_rows
        ]
        != expected_domains
    ):
        fail(
            "domain CSV identity mismatch"
        )

    for row in domain_rows:
        if (
            row[
                "status"
            ]
            != "COMPLETE_TO_PHASE2_SCOPE"
        ):
            fail(
                "domain CSV status mismatch"
            )

    #
    # Mission clock
    #

    anchors = {
        item[
            "event_id"
        ]:
            item
        for item in reference[
            "mission_clock_anchors"
        ]
    }

    required_anchors = [
        "launch",
        "otc3",
        "lunar_soi_entry",
        "pericynthion",
        "reported_earthrise",
        "lunar_soi_exit",
        "rtc1",
        "rtc2",
        "rtc3",
        "entry_interface",
        "splashdown",
    ]

    if (
        list(
            anchors
        )
        != required_anchors
    ):
        fail(
            "mission-clock anchor set changed"
        )

    fd_anchors = (
        flight_dynamics[
            "mission_anchors"
        ]
    )

    expected_direct_anchors = {
        "launch":
            "2026-04-01T22:35:12Z",

        "lunar_soi_entry":
            "2026-04-06T04:38:07.532302Z",

        "pericynthion":
            "2026-04-06T23:00:46.177998Z",

        "lunar_soi_exit":
            "2026-04-07T17:23:41.922211Z",

        "entry_interface":
            "2026-04-10T23:53:00Z",

        "splashdown":
            "2026-04-11T00:07:00Z",
    }

    for event_id, expected in (
        expected_direct_anchors.items()
    ):
        if (
            anchors[
                event_id
            ][
                "timestamp_utc"
            ]
            != expected
            or fd_anchors[
                event_id
            ][
                "timestamp_utc"
            ]
            != expected
        ):
            fail(
                f"mission anchor mismatch: {event_id}"
            )

    maneuver_correlations = {
        item[
            "maneuver_id"
        ]:
            item
        for item in (
            flight_dynamics[
                "maneuver_correlations"
            ]
        )
    }

    expected_maneuvers = {
        "otc3":
            "2026-04-06T03:03:00Z",

        "rtc1":
            "2026-04-08T00:03:00Z",

        "rtc2":
            "2026-04-10T02:53:00Z",

        "rtc3":
            "2026-04-10T18:53:00Z",
    }

    for maneuver_id, expected in (
        expected_maneuvers.items()
    ):
        if (
            anchors[
                maneuver_id
            ][
                "timestamp_utc"
            ]
            != expected
            or maneuver_correlations[
                maneuver_id
            ][
                "timestamp_utc"
            ]
            != expected
        ):
            fail(
                f"maneuver clock mismatch: {maneuver_id}"
            )

    #
    # Communications
    #

    lunar_thread = get_thread(
        communications[
            "threads"
        ],
        "lunar_occultation_blackout_and_reacquisition",
    )

    if (
        lunar_thread[
            "classification"
        ]
        != "EXPECTED_OPERATIONAL_CONSTRAINT"
        or lunar_thread[
            "anomaly"
        ]
        is not False
    ):
        fail(
            "expected lunar blackout boundary failed"
        )

    earthrise = get_step(
        lunar_thread,
        "reported_earthrise",
    )

    if (
        anchors[
            "reported_earthrise"
        ][
            "timestamp_utc"
        ]
        != earthrise[
            "timestamp_utc"
        ]
        or anchors[
            "reported_earthrise"
        ][
            "timestamp_utc"
        ]
        != "2026-04-06T23:24:00Z"
    ):
        fail(
            "Earthrise correlation failed"
        )

    fd9_thread = get_thread(
        communications[
            "threads"
        ],
        "flight_day_9_return_link_loss_and_recovery",
    )

    if (
        fd9_thread[
            "anomaly"
        ]
        is not True
        or fd9_thread[
            "causal_relationship"
        ]
        != "NOT_ESTABLISHED"
        or fd9_thread[
            "complete_two_way_outage_established"
        ]
        is not False
        or fd9_thread[
            "public_root_cause_available"
        ]
        is not False
        or fd9_thread[
            "failed_subsystem_identified"
        ]
        is not False
    ):
        fail(
            "Flight Day 9 communications boundary failed"
        )

    comm_boundary = (
        reference[
            "communications_boundary"
        ]
    )

    if (
        comm_boundary[
            "expected_lunar_blackout_classified_as_anomaly"
        ]
        is not False
        or comm_boundary[
            "flight_day_9_return_link_loss_classified_as_anomaly"
        ]
        is not True
        or comm_boundary[
            "flight_day_9_complete_two_way_outage_established"
        ]
        is not False
        or comm_boundary[
            "flight_day_9_root_cause_public"
        ]
        is not False
        or comm_boundary[
            "flight_day_9_failed_subsystem_public"
        ]
        is not False
        or comm_boundary[
            "flight_day_9_recovery_before_rtc2"
        ]
        is not True
        or comm_boundary[
            "communications_anomaly_caused_rtc2_issue"
        ]
        is not False
    ):
        fail(
            "integrated communications boundary failed"
        )

    #
    # Propulsion
    #

    architecture = (
        propulsion[
            "architecture"
        ]
    )

    if (
        architecture[
            "engine_class_count"
        ]
        != 3
        or architecture[
            "total_engine_count"
        ]
        != 33
    ):
        fail(
            "propulsion architecture mismatch"
        )

    engine_counts = {
        item[
            "engine_class_id"
        ]:
            item[
                "count"
            ]
        for item in architecture[
            "engine_classes"
        ]
    }

    if (
        engine_counts
        != {
            "main_engine_oms_e": 1,
            "auxiliary_r4d11": 8,
            "reaction_control_system": 24,
        }
    ):
        fail(
            "propulsion engine counts mismatch"
        )

    propulsion_boundary = (
        reference[
            "propulsion_boundary"
        ]
    )

    if (
        propulsion_boundary[
            "resolved_correction_burn_engine_assignments"
        ]
        != 0
        or propulsion_boundary[
            "unresolved_correction_burn_engine_assignments"
        ]
        != [
            "otc3",
            "rtc1",
            "rtc2",
            "rtc3",
        ]
        or propulsion_boundary[
            "confirmed_major_burn_engine_assignment_generalized_to_corrections"
        ]
        is not False
    ):
        fail(
            "propulsion assignment boundary failed"
        )

    #
    # Maneuvers
    #

    maneuver_summary = (
        maneuvers[
            "mission_summary"
        ]
    )

    q = reference[
        "phase2_quantitative_summary"
    ]

    expected_quantities = {
        "planned_trajectory_correction_opportunities":
            6,

        "executed_trajectory_corrections":
            4,

        "cancelled_trajectory_corrections":
            2,

        "known_executed_correction_firing_time_seconds":
            49.5,

        "return_scalar_delta_v_magnitude_sum_ft_s":
            11.1,

        "return_scalar_delta_v_magnitude_sum_m_s":
            3.38328,

        "correction_burn_engine_assignments_resolved":
            0,

        "correction_burn_engine_assignments_unresolved":
            4,

        "onboard_navigation_sensor_classes":
            6,

        "oem_maneuver_creation_brackets_audited":
            4,

        "oem_same_epoch_solution_comparisons_available":
            3,

        "gnc_operational_threads":
            5,

        "phase2_integrated_operational_threads":
            6,
    }

    for key, expected in (
        expected_quantities.items()
    ):
        if (
            q[
                key
            ]
            != expected
        ):
            fail(
                f"quantitative summary mismatch: {key}"
            )

    if (
        maneuver_summary[
            "planned_correction_opportunities"
        ]
        != 6
        or maneuver_summary[
            "executed_corrections"
        ]
        != 4
        or maneuver_summary[
            "cancelled_corrections"
        ]
        != 2
        or maneuver_summary[
            "known_executed_correction_firing_time_seconds"
        ]
        != 49.5
        or maneuver_summary[
            "return_scalar_delta_v_magnitude_sum_ft_s"
        ]
        != 11.1
    ):
        fail(
            "Phase 2I maneuver accounting mismatch"
        )

    if (
        q[
            "net_vector_delta_v_computed"
        ]
        is not False
        or q[
            "all_correction_scalar_delta_v_computed"
        ]
        is not False
    ):
        fail(
            "unsupported delta-v aggregate introduced"
        )

    #
    # OEM
    #

    if (
        len(
            flight_dynamics[
                "oem_creation_time_brackets"
            ]
        )
        != 4
    ):
        fail(
            "OEM bracket count mismatch"
        )

    comparison_count = sum(
        1
        for item in (
            flight_dynamics[
                "oem_creation_time_brackets"
            ]
        )
        if item[
            "same_epoch_solution_difference"
        ][
            "available"
        ]
    )

    if (
        comparison_count
        != 3
    ):
        fail(
            "OEM comparison count mismatch"
        )

    oem = reference[
        "oem_boundary"
    ]

    if (
        oem[
            "maneuver_brackets_audited"
        ]
        != 4
        or oem[
            "same_epoch_solution_comparisons_available"
        ]
        != 3
        or oem[
            "solution_difference_is_navigation_error"
        ]
        is not False
        or oem[
            "solution_difference_is_measured_burn_delta_v"
        ]
        is not False
        or oem[
            "creation_time_proves_maneuver_assimilation"
        ]
        is not False
        or oem[
            "maneuver_assimilation_status"
        ]
        != "NOT_ESTABLISHED"
    ):
        fail(
            "OEM non-inference boundary failed"
        )

    #
    # GNC
    #

    if (
        gnc[
            "core_architecture"
        ][
            "onboard_navigation_sensor_count"
        ]
        != 6
        or len(
            gnc[
                "operational_threads"
            ]
        )
        != 5
        or gnc[
            "phase2j_cross_phase_closure"
        ][
            "phase2j4"
        ][
            "status"
        ]
        != "COMPLETE"
    ):
        fail(
            "Phase 2J closure mismatch"
        )

    expected_state_boundary = (
        "ONBOARD_NAVIGATION_STATE != "
        "GROUND_ORBIT_DETERMINATION != "
        "AROW_PUBLIC_STATE_VECTOR"
    )

    if (
        gnc[
            "state_product_boundary"
        ][
            "statement"
        ]
        != expected_state_boundary
        or reference[
            "navigation_boundary"
        ][
            "state_product_boundary"
        ]
        != expected_state_boundary
        or reference[
            "navigation_boundary"
        ][
            "dsn_onboard_sensor"
        ]
        is not False
        or reference[
            "navigation_boundary"
        ][
            "complete_onboard_filter_state_history_public"
        ]
        is not False
    ):
        fail(
            "GNC navigation boundary failed"
        )

    #
    # Integrated threads
    #

    expected_thread_ids = [
        "earth_departure_and_adaptive_outbound_trajectory_management",
        "proximity_operations_manual_control_and_navigation",
        "deep_space_navigation_and_lunar_communications_constraint",
        "return_trajectory_refinement",
        "rtc2_communications_anomaly_recovery_and_mission_continuation",
        "final_correction_to_entry_handoff",
    ]

    threads = (
        reference[
            "phase2_integrated_operational_threads"
        ]
    )

    if (
        [
            item[
                "thread_id"
            ]
            for item in threads
        ]
        != expected_thread_ids
    ):
        fail(
            "integrated thread identity mismatch"
        )

    if (
        len(
            thread_rows
        )
        != 6
    ):
        fail(
            "integrated thread CSV row count mismatch"
        )

    if (
        [
            row[
                "thread_id"
            ]
            for row in thread_rows
        ]
        != expected_thread_ids
    ):
        fail(
            "integrated thread CSV identity mismatch"
        )

    anomalies = [
        item
        for item in threads
        if item[
            "anomaly"
        ]
    ]

    if (
        len(
            anomalies
        )
        != 1
        or anomalies[
            0
        ][
            "thread_id"
        ]
        != "rtc2_communications_anomaly_recovery_and_mission_continuation"
    ):
        fail(
            "integrated anomaly classification mismatch"
        )

    final_thread = get_thread(
        threads,
        "final_correction_to_entry_handoff",
    )

    if (
        final_thread[
            "rtc3_timestamp_utc"
        ]
        != "2026-04-10T18:53:00Z"
        or final_thread[
            "entry_interface_timestamp_utc"
        ]
        != "2026-04-10T23:53:00Z"
        or final_thread[
            "rtc3_to_entry_interval_seconds"
        ]
        != 18000.0
        or final_thread[
            "splashdown_timestamp_utc"
        ]
        != "2026-04-11T00:07:00Z"
    ):
        fail(
            "final Phase 2 handoff mismatch"
        )

    #
    # Closure and downstream handoff
    #

    criteria = (
        reference[
            "phase2_closure_criteria"
        ]
    )

    for key, value in (
        criteria.items()
    ):
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
        "DETAILED_AS_FLOWN_ENTRY_GUIDANCE"
        not in reference[
            "phase2_not_reconstructable"
        ]
    ):
        fail(
            "entry-guidance evidence boundary missing"
        )

    for key, item in (
        reference[
            "next_phase_handoffs"
        ].items()
    ):
        if (
            item[
                "status"
            ]
            != "READY"
        ):
            fail(
                f"downstream handoff not ready: {key}"
            )

    if (
        reference[
            "next_phase_handoffs"
        ][
            "phase4_entry_descent_splashdown_recovery"
        ][
            "entry_anchor_utc"
        ]
        != "2026-04-10T23:53:00Z"
    ):
        fail(
            "Phase 4 entry anchor mismatch"
        )

    #
    # Summary
    #

    if (
        summary[
            "product_id"
        ]
        != "phase2k_integrated_operations_analysis"
    ):
        fail(
            "summary product ID mismatch"
        )

    if (
        summary[
            "phase"
        ]
        != "2K"
        or summary[
            "phase_status"
        ]
        != reference[
            "phase2_status"
        ]
    ):
        fail(
            "summary phase status mismatch"
        )

    if (
        summary[
            "mission_clock_anchor_count"
        ]
        != 11
        or summary[
            "integrated_operational_thread_count"
        ]
        != 6
        or summary[
            "anomaly_thread_count"
        ]
        != 1
    ):
        fail(
            "summary aggregate mismatch"
        )

    if (
        summary[
            "integrated_operational_thread_ids"
        ]
        != expected_thread_ids
    ):
        fail(
            "summary thread identity mismatch"
        )

    expected_generated = [
        "data/processed/phase2/phase2_integrated_operational_threads.csv",
        "data/processed/phase2/phase2_domain_closure.csv",
        "data/processed/phase2/phase2_integrated_operations_summary.json",
        "docs/assets/phase2/phase2k_integrated_operational_threads.svg",
        "docs/assets/phase2/phase2k_domain_closure.svg",
    ]

    if (
        summary[
            "generated_products"
        ]
        != expected_generated
    ):
        fail(
            "generated product manifest mismatch"
        )

    validate_svg(
        THREAD_FIGURE
    )

    validate_svg(
        DOMAIN_FIGURE
    )

    print(
        "Phase 2K Artemis II Phase 2 Integration & Closure Validation"
    )

    print(
        "=" * 72
    )

    print()
    print("Reference dataset: PASS")
    print("Flight dynamics integration: PASS")
    print("Communications integration: PASS")
    print("Propulsion integration: PASS")
    print("Maneuver integration: PASS")
    print("GNC integration: PASS")
    print("Shared mission clock: PASS")
    print("Mission-clock anchors: PASS")
    print("Expected blackout classification: PASS")
    print("RTC2 anomaly/recovery boundary: PASS")
    print("Correction-engine assignment boundary: PASS")
    print("OEM solution-evolution boundary: PASS")
    print("Navigation state-product boundary: PASS")
    print("Six integrated operational threads: PASS")
    print("Final correction-to-entry handoff: PASS")
    print("Downstream phase handoffs: PASS")
    print("Processed products: PASS")
    print("Documentation figures: PASS")
    print()
    print(
        "PHASE 2K VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()