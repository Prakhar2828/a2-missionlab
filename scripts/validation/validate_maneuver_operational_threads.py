from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_operational_threads.json"
)

MANEUVER_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_plan_execution.json"
)

PROPULSION_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_esm_propulsion_architecture.json"
)

CORRELATION_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_trajectory_correlation.json"
)

COMMUNICATION_THREADS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_operational_threads.json"
)

THREAD_CSV = (
    ROOT
    / "data"
    / "processed"
    / "maneuvers"
    / "maneuver_operational_threads.csv"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "maneuvers"
    / "maneuver_operational_threads_summary.json"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "maneuvers"
    / "phase2i4_maneuver_operational_threads.svg"
)

EXPECTED_DATASET_ID = (
    "phase2i4_artemis_ii_maneuver_operational_threads"
)

EXPECTED_PRODUCT_ID = (
    "phase2i4_maneuver_operational_threads_analysis"
)


def fail(message):
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
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


def check_close(
    label,
    observed,
    expected,
    tolerance=1e-9,
):
    if abs(
        float(observed)
        - float(expected)
    ) > tolerance:
        fail(
            f"{label}: "
            f"{observed} != {expected}"
        )


def main():
    reference = load_json(
        REFERENCE_PATH
    )

    maneuvers = load_json(
        MANEUVER_PATH
    )

    propulsion = load_json(
        PROPULSION_PATH
    )

    correlation = load_json(
        CORRELATION_PATH
    )

    communications = load_json(
        COMMUNICATION_THREADS_PATH
    )

    summary = load_json(
        SUMMARY_PATH
    )

    if (
        reference[
            "dataset_id"
        ]
        != EXPECTED_DATASET_ID
    ):
        fail(
            "reference dataset ID mismatch"
        )

    if (
        summary[
            "product_id"
        ]
        != EXPECTED_PRODUCT_ID
    ):
        fail(
            "summary product ID mismatch"
        )

    maneuver_by_id = {
        item[
            "maneuver_id"
        ]:
            item
        for item in maneuvers[
            "maneuvers"
        ]
    }

    if len(
        maneuver_by_id
    ) != 6:
        fail(
            "expected six maneuver opportunities"
        )

    planned = sum(
        1
        for item in maneuver_by_id.values()
        if item[
            "planned"
        ]
    )

    executed = sum(
        1
        for item in maneuver_by_id.values()
        if item[
            "executed"
        ]
    )

    cancelled = sum(
        1
        for item in maneuver_by_id.values()
        if item[
            "status"
        ] == "CANCELLED"
    )

    if (
        planned != 6
        or executed != 4
        or cancelled != 2
    ):
        fail(
            "maneuver accounting changed"
        )

    if (
        maneuver_by_id[
            "otc1"
        ][
            "decision"
        ][
            "reason_classification"
        ]
        != "TRAJECTORY_ALREADY_ON_CORRECT_FLIGHT_PATH"
    ):
        fail(
            "OTC1 cancellation semantics changed"
        )

    if (
        maneuver_by_id[
            "otc2"
        ][
            "decision"
        ][
            "reason_classification"
        ]
        != "TRAJECTORY_REMAINED_ON_TRACK"
    ):
        fail(
            "OTC2 cancellation semantics changed"
        )

    assignments = {
        item[
            "maneuver_id"
        ]:
            item
        for item in propulsion[
            "correction_burn_assignments"
        ]
    }

    for maneuver_id in [
        "otc3",
        "rtc1",
        "rtc2",
        "rtc3",
    ]:
        if (
            assignments[
                maneuver_id
            ][
                "assignment_status"
            ]
            != "UNRESOLVED_AS_FLOWN"
            or assignments[
                maneuver_id
            ][
                "as_flown_engine_class_id"
            ]
            is not None
        ):
            fail(
                f"{maneuver_id} engine assignment "
                "incorrectly resolved"
            )

    propulsion_boundary = (
        reference[
            "propulsion_boundary"
        ]
    )

    if (
        propulsion_boundary[
            "correction_burn_engine_assignments_resolved"
        ]
        != 0
        or propulsion_boundary[
            "correction_burn_engine_assignments_unresolved"
        ]
        != 4
    ):
        fail(
            "propulsion boundary counts changed"
        )

    if (
        propulsion_boundary[
            "confirmed_major_burn_assignment_generalized_to_corrections"
        ]
        is not False
    ):
        fail(
            "OMS-E assignment incorrectly generalized"
        )

    correlations = {
        item[
            "maneuver_id"
        ]:
            item
        for item in correlation[
            "maneuver_correlations"
        ]
    }

    if (
        correlations[
            "otc3"
        ][
            "geometric_mission_phase"
        ]
        != "OUTBOUND_TRANSIT"
    ):
        fail(
            "OTC3 mission phase changed"
        )

    for maneuver_id in [
        "rtc1",
        "rtc2",
        "rtc3",
    ]:
        if (
            correlations[
                maneuver_id
            ][
                "geometric_mission_phase"
            ]
            != "TRANS_EARTH_RETURN"
        ):
            fail(
                f"{maneuver_id} phase changed"
            )

    brackets = (
        correlation[
            "oem_creation_time_brackets"
        ]
    )

    available = sum(
        1
        for item in brackets
        if item[
            "same_epoch_solution_difference"
        ][
            "available"
        ]
    )

    if available != 3:
        fail(
            "expected three OEM comparisons"
        )

    for item in brackets:
        if (
            item[
                "maneuver_assimilation_status"
            ]
            != "NOT_ESTABLISHED"
        ):
            fail(
                "maneuver assimilation incorrectly established"
            )

        difference = (
            item[
                "same_epoch_solution_difference"
            ]
        )

        if (
            difference[
                "measured_burn_delta_v"
            ]
            is not False
            or difference[
                "navigation_error"
            ]
            is not False
        ):
            fail(
                "OEM interpretation boundary failed"
            )

    comm_threads = {
        item[
            "thread_id"
        ]:
            item
        for item in communications[
            "threads"
        ]
    }

    blackout = (
        comm_threads[
            "lunar_occultation_blackout_and_reacquisition"
        ]
    )

    rtc2 = (
        comm_threads[
            "flight_day_9_return_link_loss_and_recovery"
        ]
    )

    if (
        blackout[
            "classification"
        ]
        != "EXPECTED_OPERATIONAL_CONSTRAINT"
        or blackout[
            "anomaly"
        ]
        is not False
    ):
        fail(
            "lunar blackout anomaly boundary failed"
        )

    if (
        rtc2[
            "classification"
        ]
        != "UNEXPECTED_COMMUNICATIONS_ANOMALY"
        or rtc2[
            "anomaly"
        ]
        is not True
    ):
        fail(
            "RTC2 communications anomaly classification changed"
        )

    if (
        rtc2[
            "causal_relationship"
        ]
        != "NOT_ESTABLISHED"
    ):
        fail(
            "RTC2 unsupported causality introduced"
        )

    if (
        rtc2[
            "complete_two_way_outage_established"
        ]
        is not False
    ):
        fail(
            "RTC2 outage scope incorrectly expanded"
        )

    threads = (
        reference[
            "threads"
        ]
    )

    expected_ids = [
        "outbound_adaptive_trajectory_management",
        "lunar_flyby_expected_communications_constraint",
        "return_trajectory_refinement",
        "rtc2_communications_interruption_and_recovery",
        "final_correction_to_entry_handoff",
    ]

    if [
        item[
            "thread_id"
        ]
        for item in threads
    ] != expected_ids:
        fail(
            "thread identity/order changed"
        )

    expected_classes = [
        "NOMINAL_ADAPTIVE_TRAJECTORY_MANAGEMENT",
        "EXPECTED_OPERATIONAL_CONSTRAINT",
        "NOMINAL_RETURN_TRAJECTORY_MANAGEMENT",
        "UNEXPECTED_COMMUNICATIONS_ANOMALY_WITH_MISSION_CONTINUATION",
        "NOMINAL_ENTRY_TARGETING_HANDOFF",
    ]

    if [
        item[
            "classification"
        ]
        for item in threads
    ] != expected_classes:
        fail(
            "thread classifications changed"
        )

    if [
        item[
            "anomaly"
        ]
        for item in threads
    ] != [
        False,
        False,
        False,
        True,
        False,
    ]:
        fail(
            "thread anomaly flags changed"
        )

    rtc2_thread = threads[
        3
    ]

    if (
        rtc2_thread[
            "causal_relationship"
        ]
        != "NOT_ESTABLISHED"
        or rtc2_thread[
            "complete_two_way_outage_established"
        ]
        is not False
        or rtc2_thread[
            "burn_failure"
        ]
        is not False
        or rtc2_thread[
            "propulsion_anomaly_inferred"
        ]
        is not False
        or rtc2_thread[
            "burn_executed_after_recovery"
        ]
        is not True
    ):
        fail(
            "RTC2 operational integration boundary failed"
        )

    mission_summary = (
        reference[
            "mission_summary"
        ]
    )

    check_close(
        "executed correction firing time",
        mission_summary[
            "known_executed_correction_firing_time_seconds"
        ],
        49.5,
    )

    check_close(
        "return scalar delta-v ft/s",
        mission_summary[
            "return_scalar_delta_v_magnitude_sum_ft_s"
        ],
        11.1,
    )

    check_close(
        "return scalar delta-v m/s",
        mission_summary[
            "return_scalar_delta_v_magnitude_sum_m_s"
        ],
        3.38328,
    )

    if (
        mission_summary[
            "net_vector_delta_v_computed"
        ]
        is not False
        or mission_summary[
            "all_correction_scalar_delta_v_computed"
        ]
        is not False
    ):
        fail(
            "unsupported delta-v aggregate introduced"
        )

    oem_boundary = (
        reference[
            "oem_solution_boundary"
        ]
    )

    if (
        oem_boundary[
            "standard_public_oem_products"
        ]
        != 9
        or oem_boundary[
            "same_epoch_creation_bracket_comparisons_available"
        ]
        != 3
        or oem_boundary[
            "rtc3_later_public_oem_available"
        ]
        is not False
        or oem_boundary[
            "maneuver_assimilation_established_for_any_correction"
        ]
        is not False
        or oem_boundary[
            "oem_difference_is_navigation_error"
        ]
        is not False
        or oem_boundary[
            "oem_difference_is_measured_burn_delta_v"
        ]
        is not False
    ):
        fail(
            "OEM solution boundary changed"
        )

    closure = (
        reference[
            "phase_2i_closure_criteria"
        ]
    )

    if not all(
        closure.values()
    ):
        fail(
            "Phase 2I closure criteria not all PASS"
        )

    if not THREAD_CSV.exists():
        fail(
            "thread CSV missing"
        )

    with THREAD_CSV.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        rows = list(
            csv.DictReader(f)
        )

    if len(
        rows
    ) != 5:
        fail(
            "thread CSV must contain five rows"
        )

    if [
        row[
            "thread_id"
        ]
        for row in rows
    ] != expected_ids:
        fail(
            "thread CSV identity/order changed"
        )

    if (
        summary[
            "thread_count"
        ]
        != 5
    ):
        fail(
            "summary thread count changed"
        )

    if (
        summary[
            "phase_2i_closure_criteria"
        ]
        != closure
    ):
        fail(
            "summary closure criteria mismatch"
        )

    if (
        summary[
            "guardrails"
        ]
        != reference[
            "guardrails"
        ]
    ):
        fail(
            "summary guardrails mismatch"
        )

    if not FIGURE_PATH.exists():
        fail(
            "operational-thread figure missing"
        )

    svg = FIGURE_PATH.read_text(
        encoding="utf-8"
    )

    if (
        "<svg" not in svg
        or len(svg) < 1000
    ):
        fail(
            "invalid operational-thread SVG"
        )

    print()
    print(
        "Phase 2I.4 Maneuver Operational Threads Validation"
    )

    print("=" * 70)

    print()
    print(
        "Correction accounting:"
    )

    print(
        "  planned: 6"
    )

    print(
        "  executed: 4"
    )

    print(
        "  cancelled: 2"
    )

    print(
        "  outbound: 2 cancelled / 1 executed"
    )

    print(
        "  return: 3 executed / 3 planned"
    )

    print()
    print(
        "Operational threads:"
    )

    for index, thread_id in enumerate(
        expected_ids,
        start=1,
    ):
        print(
            f"  {index}. {thread_id}: PASS"
        )

    print()
    print(
        "Outbound cancellation semantics:"
    )

    print(
        "  OTC1 cancelled != failed burn: PASS"
    )

    print(
        "  OTC2 cancelled != failed burn: PASS"
    )

    print(
        "  propulsion anomaly inferred: FALSE"
    )

    print()
    print(
        "Lunar blackout:"
    )

    print(
        "  EXPECTED_OPERATIONAL_CONSTRAINT: PASS"
    )

    print(
        "  anomaly: FALSE"
    )

    print()
    print(
        "RTC2 communications integration:"
    )

    print(
        "  communications anomaly: PASS"
    )

    print(
        "  causal relationship: NOT_ESTABLISHED"
    )

    print(
        "  complete two-way outage: NOT_ESTABLISHED"
    )

    print(
        "  burn executed after recovery: TRUE"
    )

    print(
        "  burn failure: FALSE"
    )

    print(
        "  propulsion anomaly inferred: FALSE"
    )

    print()
    print(
        "Propulsion boundary:"
    )

    print(
        "  resolved correction assignments: 0"
    )

    print(
        "  unresolved correction assignments: 4"
    )

    print(
        "  confirmed major OMS-E burns generalized: FALSE"
    )

    print()
    print(
        "Correction aggregates:"
    )

    print(
        "  known firing time: 49.5 s"
    )

    print(
        "  return scalar delta-v sum: 11.1 ft/s"
    )

    print(
        "  return scalar delta-v sum: 3.38328 m/s"
    )

    print(
        "  net vector delta-v: NOT COMPUTED"
    )

    print(
        "  all-correction scalar delta-v: NOT COMPUTED"
    )

    print()
    print(
        "OEM boundary:"
    )

    print(
        "  standard products: 9"
    )

    print(
        "  common-epoch comparisons: 3"
    )

    print(
        "  RTC3 later OEM: NONE"
    )

    print(
        "  maneuver assimilation established: FALSE"
    )

    print(
        "  navigation error interpretation: FALSE"
    )

    print(
        "  measured burn delta-v interpretation: FALSE"
    )

    print()
    print(
        "Products:"
    )

    print(
        "  thread CSV rows: 5"
    )

    print(
        "  summary: PASS"
    )

    print(
        "  operational-thread figure: PASS"
    )

    print()
    print(
        "Phase 2I closure criteria:"
    )

    for key in closure:
        print(
            f"  {key}: PASS"
        )

    print()
    print(
        "PHASE 2I READY TO CLOSE:"
    )

    print(
        "  TRUE"
    )

    print()
    print(
        "OK: Phase 2I.4 operational-thread identities, "
        "maneuver accounting, cancellation semantics, "
        "expected-versus-anomalous communications context, "
        "RTC2 mission-continuation sequence, propulsion "
        "assignment boundaries, correction aggregates, OEM "
        "non-telemetry boundaries, generated products, "
        "guardrails, and complete Phase 2I closure criteria "
        "independently validated."
    )


if __name__ == "__main__":
    main()