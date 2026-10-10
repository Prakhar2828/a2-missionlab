from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


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

plt.rcParams[
    "svg.hashsalt"
] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path):
    if not path.exists():
        fail(
            f"Missing required file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


def normalize_svg(path: Path) -> None:
    text = path.read_text(
        encoding="utf-8",
    )

    path.write_text(
        "\n".join(
            line.rstrip(" \t")
            for line in text.splitlines()
        )
        + "\n",
        encoding="utf-8",
    )


def build_figure(threads) -> None:
    FIGURE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(17, 10)
    )

    ax.set_xlim(
        0,
        1,
    )

    ax.set_ylim(
        0,
        1,
    )

    ax.axis(
        "off"
    )

    ax.set_title(
        "Artemis II Maneuver and Propulsion Operational Threads",
        fontsize=16,
        pad=18,
    )

    y_positions = [
        0.82,
        0.66,
        0.50,
        0.34,
        0.18,
    ]

    for thread, y in zip(
        threads,
        y_positions,
    ):
        anomaly_text = (
            "ANOMALY"
            if thread[
                "anomaly"
            ]
            else "NOMINAL / EXPECTED"
        )

        sequence = " → ".join(
            step[
                "step_id"
            ]
            for step in thread[
                "operational_sequence"
            ]
        )

        text = (
            f"{thread['name']}\n"
            f"{thread['classification']} | "
            f"{anomaly_text}\n"
            f"{sequence}"
        )

        ax.text(
            0.5,
            y,
            text,
            ha="center",
            va="center",
            fontsize=8.5,
            bbox={
                "boxstyle":
                    "round,pad=0.55",

                "fill":
                    False,
            },
        )

    ax.text(
        0.5,
        0.045,
        (
            "Operational threads reconstruct public evidence sequences. "
            "They are not console logs, Flight Director rationale trees, "
            "root-cause analyses, burn telemetry, or complete targeting logic."
        ),
        ha="center",
        va="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        FIGURE_PATH,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        FIGURE_PATH
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

    if (
        reference.get(
            "dataset_id"
        )
        != (
            "phase2i4_artemis_ii_"
            "maneuver_operational_threads"
        )
    ):
        fail(
            "Unexpected Phase 2I.4 dataset ID."
        )

    if (
        maneuvers.get(
            "dataset_id"
        )
        != (
            "phase2i1_artemis_ii_"
            "maneuver_plan_execution"
        )
    ):
        fail(
            "Unexpected Phase 2I.1 dataset ID."
        )

    if (
        propulsion.get(
            "dataset_id"
        )
        != (
            "phase2i2_artemis_ii_"
            "esm_propulsion_architecture"
        )
    ):
        fail(
            "Unexpected Phase 2I.2 dataset ID."
        )

    if (
        correlation.get(
            "dataset_id"
        )
        != (
            "phase2i3_artemis_ii_"
            "maneuver_trajectory_correlation"
        )
    ):
        fail(
            "Unexpected Phase 2I.3 dataset ID."
        )

    if (
        communications.get(
            "dataset_id"
        )
        != (
            "phase2h4_artemis_ii_"
            "communications_operational_threads"
        )
    ):
        fail(
            "Unexpected Phase 2H.4 dataset ID."
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

    expected_maneuver_ids = [
        "otc1",
        "otc2",
        "otc3",
        "rtc1",
        "rtc2",
        "rtc3",
    ]

    if list(
        maneuver_by_id
    ) != expected_maneuver_ids:
        fail(
            "Maneuver identity/order changed."
        )

    planned_count = sum(
        1
        for item in maneuver_by_id.values()
        if item[
            "planned"
        ]
    )

    executed_count = sum(
        1
        for item in maneuver_by_id.values()
        if item[
            "executed"
        ]
    )

    cancelled_count = sum(
        1
        for item in maneuver_by_id.values()
        if item[
            "status"
        ] == "CANCELLED"
    )

    if (
        planned_count != 6
        or executed_count != 4
        or cancelled_count != 2
    ):
        fail(
            "Mission correction accounting changed."
        )

    summary_reference = (
        reference[
            "mission_summary"
        ]
    )

    if (
        summary_reference[
            "planned_correction_opportunities"
        ]
        != planned_count
        or summary_reference[
            "executed_corrections"
        ]
        != executed_count
        or summary_reference[
            "cancelled_corrections"
        ]
        != cancelled_count
    ):
        fail(
            "Phase 2I.4 summary accounting mismatch."
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
            "OTC1 cancellation reason changed."
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
            "OTC2 cancellation reason changed."
        )

    correction_assignments = {
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
        assignment = (
            correction_assignments[
                maneuver_id
            ]
        )

        if (
            assignment[
                "assignment_status"
            ]
            != "UNRESOLVED_AS_FLOWN"
            or assignment[
                "as_flown_engine_class_id"
            ]
            is not None
        ):
            fail(
                f"{maneuver_id} engine assignment "
                "unexpectedly resolved."
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
            "OTC3 mission phase changed."
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
                f"{maneuver_id} mission phase changed."
            )

    brackets = {
        item[
            "maneuver_id"
        ]:
            item
        for item in correlation[
            "oem_creation_time_brackets"
        ]
    }

    available_comparisons = sum(
        1
        for item in brackets.values()
        if item[
            "same_epoch_solution_difference"
        ][
            "available"
        ]
    )

    if available_comparisons != 3:
        fail(
            "Expected three OEM common-epoch comparisons."
        )

    if (
        brackets[
            "rtc3"
        ][
            "same_epoch_solution_difference"
        ][
            "available"
        ]
        is not False
    ):
        fail(
            "RTC3 unexpectedly gained later OEM comparison."
        )

    for item in brackets.values():
        if (
            item[
                "maneuver_assimilation_status"
            ]
            != "NOT_ESTABLISHED"
        ):
            fail(
                "Unsupported maneuver-assimilation "
                "conclusion introduced."
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
                "OEM interpretation boundary changed."
            )

    communication_threads = {
        item[
            "thread_id"
        ]:
            item
        for item in communications[
            "threads"
        ]
    }

    blackout = (
        communication_threads[
            "lunar_occultation_blackout_and_reacquisition"
        ]
    )

    rtc2_comms = (
        communication_threads[
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
            "Lunar blackout classification changed."
        )

    if (
        rtc2_comms[
            "classification"
        ]
        != "UNEXPECTED_COMMUNICATIONS_ANOMALY"
        or rtc2_comms[
            "anomaly"
        ]
        is not True
    ):
        fail(
            "RTC2 communications classification changed."
        )

    if (
        rtc2_comms[
            "causal_relationship"
        ]
        != "NOT_ESTABLISHED"
    ):
        fail(
            "Unsupported RTC2 communications causality introduced."
        )

    if (
        rtc2_comms[
            "complete_two_way_outage_established"
        ]
        is not False
    ):
        fail(
            "RTC2 return-link event incorrectly "
            "promoted to complete two-way outage."
        )

    expected_sequence = [
        "unexpected_return_link_loss",
        "two_way_communications_reestablished",
        "burn_preparation_resumed",
        "rtc2",
    ]

    observed_sequence = [
        item[
            "step_id"
        ]
        for item in rtc2_comms[
            "operational_sequence"
        ]
    ]

    if (
        observed_sequence
        != expected_sequence
    ):
        fail(
            "RTC2 communications operational sequence changed."
        )

    threads = (
        reference[
            "threads"
        ]
    )

    expected_thread_ids = [
        "outbound_adaptive_trajectory_management",
        "lunar_flyby_expected_communications_constraint",
        "return_trajectory_refinement",
        "rtc2_communications_interruption_and_recovery",
        "final_correction_to_entry_handoff",
    ]

    if [
        thread[
            "thread_id"
        ]
        for thread in threads
    ] != expected_thread_ids:
        fail(
            "Operational-thread identity/order changed."
        )

    expected_classifications = {
        "outbound_adaptive_trajectory_management":
            "NOMINAL_ADAPTIVE_TRAJECTORY_MANAGEMENT",

        "lunar_flyby_expected_communications_constraint":
            "EXPECTED_OPERATIONAL_CONSTRAINT",

        "return_trajectory_refinement":
            "NOMINAL_RETURN_TRAJECTORY_MANAGEMENT",

        "rtc2_communications_interruption_and_recovery":
            (
                "UNEXPECTED_COMMUNICATIONS_ANOMALY_"
                "WITH_MISSION_CONTINUATION"
            ),

        "final_correction_to_entry_handoff":
            "NOMINAL_ENTRY_TARGETING_HANDOFF",
    }

    expected_anomaly = {
        "outbound_adaptive_trajectory_management":
            False,

        "lunar_flyby_expected_communications_constraint":
            False,

        "return_trajectory_refinement":
            False,

        "rtc2_communications_interruption_and_recovery":
            True,

        "final_correction_to_entry_handoff":
            False,
    }

    for thread in threads:
        thread_id = (
            thread[
                "thread_id"
            ]
        )

        if (
            thread[
                "classification"
            ]
            != expected_classifications[
                thread_id
            ]
        ):
            fail(
                f"{thread_id} classification changed."
            )

        if (
            thread[
                "anomaly"
            ]
            is not expected_anomaly[
                thread_id
            ]
        ):
            fail(
                f"{thread_id} anomaly flag changed."
            )

    rtc2_thread = next(
        thread
        for thread in threads
        if thread[
            "thread_id"
        ]
        == "rtc2_communications_interruption_and_recovery"
    )

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
            "RTC2 integration boundary changed."
        )

    mission_summary = (
        reference[
            "mission_summary"
        ]
    )

    executed_time = sum(
        float(
            maneuver_by_id[
                maneuver_id
            ][
                "execution"
            ][
                "duration_seconds"
            ]
        )
        for maneuver_id in [
            "otc3",
            "rtc1",
            "rtc2",
            "rtc3",
        ]
    )

    if abs(
        executed_time
        - 49.5
    ) > 1e-9:
        fail(
            "Known correction firing-time aggregate changed."
        )

    if abs(
        mission_summary[
            "known_executed_correction_firing_time_seconds"
        ]
        - 49.5
    ) > 1e-9:
        fail(
            "Reference firing-time aggregate changed."
        )

    return_delta_v = sum(
        float(
            maneuver_by_id[
                maneuver_id
            ][
                "execution"
            ][
                "reported_delta_v_ft_s"
            ]
        )
        for maneuver_id in [
            "rtc1",
            "rtc2",
            "rtc3",
        ]
    )

    if abs(
        return_delta_v
        - 11.1
    ) > 1e-9:
        fail(
            "Return scalar delta-v sum changed."
        )

    if abs(
        mission_summary[
            "return_scalar_delta_v_magnitude_sum_ft_s"
        ]
        - 11.1
    ) > 1e-9:
        fail(
            "Reference return scalar delta-v changed."
        )

    if abs(
        mission_summary[
            "return_scalar_delta_v_magnitude_sum_m_s"
        ]
        - 3.38328
    ) > 1e-9:
        fail(
            "Reference SI delta-v conversion changed."
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
            "Unsupported correction delta-v aggregate introduced."
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
            "One or more Phase 2I closure criteria failed."
        )

    THREAD_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = []

    for thread in threads:
        rows.append(
            {
                "thread_id":
                    thread[
                        "thread_id"
                    ],

                "name":
                    thread[
                        "name"
                    ],

                "classification":
                    thread[
                        "classification"
                    ],

                "anomaly":
                    str(
                        thread[
                            "anomaly"
                        ]
                    ).lower(),

                "step_count":
                    len(
                        thread[
                            "operational_sequence"
                        ]
                    ),

                "sequence":
                    " -> ".join(
                        step[
                            "step_id"
                        ]
                        for step in thread[
                            "operational_sequence"
                        ]
                    ),
            }
        )

    fieldnames = [
        "thread_id",
        "name",
        "classification",
        "anomaly",
        "step_count",
        "sequence",
    ]

    with THREAD_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(
            rows
        )

    build_figure(
        threads
    )

    summary = {
        "product_id":
            "phase2i4_maneuver_operational_threads_analysis",

        "mission":
            "Artemis II",

        "reference_dataset_id":
            reference[
                "dataset_id"
            ],

        "correction_accounting": {
            "planned":
                planned_count,

            "executed":
                executed_count,

            "cancelled":
                cancelled_count,

            "outbound_cancelled":
                2,

            "outbound_executed":
                1,

            "return_executed":
                3,
        },

        "propulsion_boundary":
            reference[
                "propulsion_boundary"
            ],

        "correction_aggregates":
            mission_summary,

        "oem_solution_boundary":
            reference[
                "oem_solution_boundary"
            ],

        "thread_count":
            len(
                threads
            ),

        "threads":
            rows,

        "phase_2i_closure_criteria":
            closure,

        "guardrails":
            reference[
                "guardrails"
            ],

        "outputs": {
            "thread_csv":
                str(
                    THREAD_CSV.relative_to(
                        ROOT
                    )
                ),

            "figure":
                str(
                    FIGURE_PATH.relative_to(
                        ROOT
                    )
                ),
        },
    }

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with SUMMARY_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            summary,
            f,
            indent=2,
        )

    print()
    print(
        "Phase 2I.4 Maneuver Operational Threads Analysis"
    )

    print("=" * 68)

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
        "  outbound cancelled: 2 of 3"
    )

    print(
        "  return executed: 3 of 3"
    )

    print()
    print(
        "Correction aggregates:"
    )

    print(
        "  known executed firing time:"
    )

    print(
        "    49.5 s"
    )

    print(
        "  return scalar delta-v magnitude sum:"
    )

    print(
        "    11.1 ft/s"
    )

    print(
        "    3.38328 m/s"
    )

    print(
        "  net vector delta-v:"
    )

    print(
        "    NOT COMPUTED"
    )

    print()
    print(
        "Propulsion assignment boundary:"
    )

    print(
        "  resolved correction assignments: 0"
    )

    print(
        "  unresolved correction assignments: 4"
    )

    print()
    print(
        "Operational threads:"
    )

    for index, thread in enumerate(
        threads,
        start=1,
    ):
        print()
        print(
            f"  {index}. "
            f"{thread['thread_id']}"
        )

        print(
            "     classification:"
        )

        print(
            "       "
            f"{thread['classification']}"
        )

        print(
            "     anomaly:"
        )

        print(
            "       "
            + (
                "TRUE"
                if thread[
                    "anomaly"
                ]
                else "FALSE"
            )
        )

        print(
            "     steps:"
        )

        print(
            "       "
            f"{len(thread['operational_sequence'])}"
        )

    print()
    print(
        "RTC2 integration:"
    )

    print(
        "  communications anomaly: TRUE"
    )

    print(
        "  causality established: FALSE"
    )

    print(
        "  complete two-way outage established: FALSE"
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
        "OEM boundary:"
    )

    print(
        "  standard products: 9"
    )

    print(
        "  same-epoch comparisons: 3"
    )

    print(
        "  RTC3 later OEM: NONE"
    )

    print(
        "  maneuver assimilation established: FALSE"
    )

    print(
        "  OEM difference = navigation error: FALSE"
    )

    print(
        "  OEM difference = measured burn delta-v: FALSE"
    )

    print()
    print(
        "Phase 2I closure:"
    )

    for key, value in (
        closure.items()
    ):
        print(
            f"  {key}: "
            + (
                "PASS"
                if value
                else "FAIL"
            )
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
        "Wrote:"
    )

    print(
        "  "
        f"{THREAD_CSV.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{SUMMARY_PATH.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{FIGURE_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()